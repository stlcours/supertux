#!/usr/bin/env python
#
# SuperTux
# Copyright (C) 2014 Ingo Ruhnke <grumbel@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import argparse
import glob
import hashlib
import os
import subprocess
import sys

import sexpr


def escape_str(string):
    return "\"%s\"" % string.replace("\"", "\\\"")


class Addon(object):
    def __init__(self, filename):
        lst = sexpr.parse(filename)
        if lst[0][0] != "supertux-addoninfo":
            raise Exception("not a supertux-addoninfo: %s" % lst[0][0])
        else:
            tags = {}
            for k, v in lst[0][1:]:
                if k == "id":
                    self.id = v
                elif k == "version":
                    self.version = int(v)
                elif k == "type":
                    self.type = v
                elif k == "title":
                    self.title = v
                elif k == "author":
                    self.author = v
                elif k == "license":
                    self.license = v
                else:
                    raise Exception("unknown tag: %s" % k)

            self.md5 = ""
            self.url = ""

    def write(self, fout):
        fout.write("  (supertux-addoninfo\n")
        fout.write("    (id %s)\n" % escape_str(self.id))
        fout.write("    (version %d)\n" % self.version)
        fout.write("    (type %s)\n" % escape_str(self.type))
        fout.write("    (title %s)\n" % escape_str(self.title))
        fout.write("    (author %s)\n" % escape_str(self.author))
        fout.write("    (license %s)\n" % escape_str(self.license))
        fout.write("    (url %s)\n" % escape_str(self.url))
        fout.write("    (md5 %s)\n" % escape_str(self.md5))
        fout.write("   )\n")


def process_addon(fout, addon_dir, nfo, base_url, zipdir):
    # print addon_dir, nfo
    with open(nfo) as fin:
        addon = Addon(fin.read())

    zipfile = addon.id + "_v" + str(addon.version) + ".zip"

    # see http://pivotallabs.com/barriers-deterministic-reproducible-zip-files/
    os.remove(os.path.join(zipdir, zipfile))
    zipout = os.path.relpath(os.path.join(zipdir, zipfile), addon_dir)
    subprocess.call(["zip", "-X", "-r", "--quiet", zipout, "."], cwd=addon_dir)

    with open(os.path.join(zipdir, zipfile), 'rb') as fin:
        addon.md5 = hashlib.md5(fin.read()).hexdigest()

    addon.url = base_url + zipfile

    addon.write(fout)


def generate_index(fout, directory, base_url, zipdir):
    fout.write(";; automatically generated by build-addon-index.py\n")
    fout.write("(supertux-addons\n")
    for addon_dir in os.listdir(directory):
        addon_dir = os.path.join(directory, addon_dir)
        if os.path.isdir(addon_dir):
            print addon_dir
            nfos = glob.glob(os.path.join(addon_dir, "*.nfo"))
            if len(nfos) == 0:
                raise Exception(".nfo file missing from %s" % addon_dir)
            elif len(nfos) > 1:
                raise Exception("to many .nfo files in %s" % addon_dir)
            else:
                try:
                    process_addon(fout, addon_dir, nfos[0], base_url, zipdir)
                except Exception, e:
                    sys.stderr.write("%s: ignoring addon because: %s\n" % (addon_dir, e))
    fout.write(")\n\n;; EOF ;;\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Addon Index/Zip Generator')
    parser.add_argument('DIRECTORY',  type=str, nargs=1,
                        help="directory containing the mods")
    parser.add_argument('-o', '--output', metavar='FILE', type=str, required=False,
                        help="output file")
    parser.add_argument('-z', '--zipdir', metavar="DIR", type=str, required=True,
                        help="generate zip files")
    parser.add_argument('-u', '--url', metavar='FILE', type=str,
                        default="https://raw.githubusercontent.com/SuperTux/addons/master/repository/",
                        help="base url")
    args = parser.parse_args()

    if args.output is None:
        fout = sys.stdout
        generate_index(fout, args.DIRECTORY[0], args.url, args.zipdir)
    else:
        with open(args.output, "w") as fout:
            generate_index(fout, args.DIRECTORY[0], args.url, args.zipdir)

# EOF #
