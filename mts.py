#!/usr/local/bin/python3
import shutil
import pprint
import zipfile
import os
import sys
import re
import requests
import datetime
import argparse
from metar import Metar

times = {
    'morning': 26400,  # 07:20
    'afternoon': 43200,  # 12:00
    'evening': 66600,  # 18:30
}

parser = argparse.ArgumentParser(description="Split your DCS mission into different times, with weather from avwx")
parser.add_argument('-m', '--mission', required=True, help="The mission you want to split")
parser.add_argument('-i', '--icao', help="The ICAO designation of the airport to get weather for")
parser.add_argument('-f', '--fallback', action='store_true',
                    help="Add this if you want to fall back to a default weather if no ICAO is found.\
                        If not specified, and no ICAO weather is found, we'll exit without doing anything")
parser.add_argument('-o', '--output', default=None, help="The directory to output the split missions to. Defaults to the current directory.")

def change_mission_data(misFile, fn, descr, time, wx):
    today = datetime.datetime.now()
    start_time_regex = re.compile("^\s{4}\[\"start_time")
    date_regex_day = re.compile("^\s+\[\"Day")
    date_regex_month = re.compile("^\s+\[\"Month")
    date_regex_year = re.compile("^\s+\[\"Year")
    wind_rgx = re.compile("^\s{16}\[\"speed")
    wind_dir_rgx = re.compile("^\s{16}\[\"dir")
    if descr == 'morning':
        next_time = 'afternoon'
    elif descr == 'afternoon':
        next_time = 'evening'
    elif descr == 'evening':
    #     next_time = 'night'
    # elif descr == 'night':
        next_time = 'morning'

    next_file = "{0}_{1}.miz".format(fn[:-4], next_time)
    this_file = "{0}_{1}.miz.tmp".format(fn[:-4], descr)

    with open(misFile, encoding='utf-8') as fp:
        in_fog = False
        with open(this_file, 'w', encoding='utf-8') as tf:
            for line in fp:
                if '["fog"]' in line:
                    in_fog = True

                if '-- end of ["fog"]' in line:
                    in_fog = False

                if fn in line:
                    line = line.replace(fn, next_file)
                if not in_fog and '["thickness"]' in line:
                    line = '            ["thickness"] = {},\n'.format(wx['cloud_height'])
                if not in_fog and '["density"]' in line:
                    line = '            ["density"] = {},\n'.format(wx['cloud_density'])
                if '["base"]' in line:
                    line = '            ["base"] = {},\n'.format(wx['cloud_base'])
                if '["iprecptns"]' in line:
                    line = '            ["iprecptns"] = {},\n'.format(wx['precip'])
                if '["qnh"]' in line:
                    line = '        ["qnh"] = {},\n'.format(max(760, wx['pressure']))
                if '["temperature"]' in line:
                    line = '            ["temperature"] = {},\n'.format(wx['temp'])
                if wind_rgx.match(line):
                    line = '                ["speed"] = {},\n'.format(wx['wind_speed'])
                if wind_dir_rgx.match(line):
                    line = '                ["dir"] = {},\n'.format(wx['wind_dir'])
                if start_time_regex.match(line):
                    line = "    [\"start_time\"] = {},\n".format(time)
                if date_regex_year.match(line):
                    line = "         [\"Year\"] = {},\n".format(today.year)
                if date_regex_day.match(line):
                    line = "         [\"Day\"] = {},\n".format(today.day)
                if date_regex_month.match(line):
                    line = "         [\"Month\"] = {},\n".format(today.month)
                tf.write(line)

    return this_file


def handle_mission(fn, dest, icao, fallback):
    def check_fallback():
        if not fallback:
            print("Fallback flag not specified, quitting.")
            sys.exit(1)
        else:
            print("Falling back to defaults")

    if os.path.exists(fn):
        path = os.path.abspath(fn)
        print("path: {}".format(path))
        basedir = os.path.dirname(path)
        print("basedir: {}".format(basedir))
        targetdir = "{}/.tmp".format(basedir)
        print("targetdir: {}".format(targetdir))
        print("Making tmp dir: {}".format(targetdir))
        if os.path.exists(targetdir):
            shutil.rmtree(targetdir)
        os.makedirs(targetdir)

        print("Extracting zip: {}".format(fn))
        zip_ref = zipfile.ZipFile(fn, 'r')
        zip_ref.extractall(targetdir)

        misfile = "{}/mission".format(targetdir)

        # Get WX
        cloud_map = {
            'FEW': 2,
            'SCT': 6,
            'BKN': 8,
            'OVC': 10
        }

        wx = {
            "temp": 23,
            "wind_speed": 4,
            "wind_dir": 170,
            "cloud_base": 8000,
            "cloud_height": 1800,
            "cloud_density": 5,
            "precip": 0,
            "pressure": 760
        }

        wx_request = requests.get("https://avwx.rest/api/metar/" + icao.upper())
        if wx_request.status_code == 200:
            try:
                wx_json = wx_request.json()
                obs = Metar.Metar(wx_json['Raw-Report'])
                #obs = Metar.Metar("URKK 211400Z 33004MPS 290V360 CAVOK 30/18 Q1011 R23L/CLRD70 NOSIG RMK QFE755")
                precip = 0
                if obs.weather:
                    if obs.weather[0][2] == 'RA':
                        precip = 1
                    if obs.weather[0][1] == 'TS':
                        precip = 2

                wx['temp'] = obs.temp.value()
                wx['wind_speed'] = obs.wind_speed.value()
                wx['wind_dir'] = (obs.wind_dir.value() + 180) % 360
                if obs.sky and obs.sky[0] != 'CLR' and obs.sky[0][0] != 'NCD':
                    wx['cloud_base'] = obs.sky[0][1].value()
                    wx['cloud_height'] = 1800
                    wx['cloud_density'] = cloud_map[obs.sky[0][0]]
                    print("CLOUD COVERAGE IS {}".format(cloud_map[obs.sky[0][0]]))
                else:
                    wx['cloud_base'] = 1800
                    wx['cloud_height'] = 1800
                    wx['cloud_density'] = 0
                wx['precip'] = precip
                wx['pressure'] = obs.press.value() / 1.33

                print(obs.string())

                pprint.pprint(wx)
            except Exception as e:
                print(e)
                print("FAILED TO GET DYNAMIC WEATHER")
                check_fallback()

        else:
            print("FAILED TO GET DYNAMIC WEATHER. METAR API UNAVAILABLE")
            check_fallback()

        new_files = []
        for descr, time in times.items():
            new_mis = change_mission_data(misfile, fn, descr, time, wx)
            new_file = "{}/{}_{}".format(
                basedir,
                fn[:-4],
                descr
            )
            print(targetdir)
            print(new_file)
            shutil.copytree(targetdir, new_file)
            shutil.move(new_mis, os.path.join(new_file, "mission"))
            shutil.make_archive(new_file, 'zip', new_file)
            new_files.append(new_file)

        new_dir = "{}/{}".format(basedir, fn)[:-4]
        print("New dir: " + new_dir)
        if os.path.exists(new_dir) and os.path.isdir(new_dir):
            shutil.rmtree(new_dir)
        os.makedirs(new_dir)

        for new_file in new_files:
            filename = new_file+".zip"
            print("new_file: " + new_file)
            shutil.move(filename, dest + "/" + os.path.basename(new_file)+".miz")
            shutil.rmtree(new_file)

        #Clean up tmp dir.
        shutil.rmtree(targetdir)


args = parser.parse_args()
file = args.mission
icao = args.icao
dest = args.output
fallback = args.fallback
handle_mission(file, dest, icao, fallback)
