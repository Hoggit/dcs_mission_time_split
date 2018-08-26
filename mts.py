#!/usr/local/bin/python3
import shutil
import zipfile
import os
import sys
import re

times = {
    'morning': 26400,  # 07:20
    'afternoon': 43200,  # 12:00
    'evening': 66600,  # 18:30
}


def change_mission_time(misFile, fn, descr, time):
    rgx = re.compile("^\s{4}\[\"start_time")
    if descr == 'morning':
        next_time = 'afternoon'
    elif descr == 'afternoon':
        next_time = 'evening'
    elif descr == 'evening':
    #     next_time = 'night'
    # elif descr == 'night':
        next_time = 'morning'

    next_file = "{0}_{1}.miz".format(fn[:-4], next_time)
    this_file = "{0}_{1}.tmp".format(fn[:-4], descr)

    with open(misFile) as fp:
        with open(this_file, 'w') as tf:
            for line in fp:
                if fn in line:
                    line = line.replace(fn, next_file)
                if rgx.match(line):
                    line = "    [\"start_time\"] = {},\n".format(time)
                tf.write(line)

    return this_file


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
            new_mis = change_mission_time(misfile, fn, descr, time)
            new_file = "{}/{}_{}".format(
                basedir,
                fn[:-4],
                descr
            )
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
            shutil.move(filename, new_dir+"/"+os.path.basename(new_file)+".miz")
            shutil.rmtree(new_file)

        #Clean up tmp dir.
        shutil.rmtree(targetdir)

files = sys.argv[1:]

for filename in files:
    handle_mission(filename)