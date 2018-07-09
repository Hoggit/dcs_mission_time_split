#!/usr/local/bin/python3
import shutil
import zipfile
import os
import sys
import fileinput
import re

times = {
    'morning': 23400,  # 06:30
    'midday': 45000,  # 12:30
    'evening': 70200  # 19:30
}


def change_mission_time(misFile, time):
    rgx = re.compile("^\s{4}\[\"start_time")
    with fileinput.input(misFile, inplace=True) as fp:
        for line in fp:
            if rgx.match(line):
                line = "    [\"start_time\"] = {},\n".format(time)
            sys.stdout.write(line)



def handle_mission(fn):
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

        new_files = []
        for descr, time in times.items():
            change_mission_time(misfile, str(time))
            new_file = "{}/{}-{}".format(
                basedir,
                fn[:-4],
                descr
            )
            shutil.make_archive(new_file, 'zip', targetdir)
            new_files.append(new_file)

        new_dir = "{}/{}".format(basedir, fn)[:-4]
        print("New dir: " + new_dir)
        if os.path.exists(new_dir) and os.path.isdir(new_dir):
            shutil.rmtree(new_dir)
        os.makedirs(new_dir)

        for new_file in new_files:
            filename = new_file+".zip"
            print("new_file: " + new_file)
            shutil.move(filename, new_dir+"/"+os.path.basename(new_file)+".miz")

        #Clean up tmp dir.
        shutil.rmtree(targetdir)

files = sys.argv[1:]

for filename in files:
    handle_mission(filename)