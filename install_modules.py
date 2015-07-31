#!/usr/bin/env python

# Install micropython modules

import argparse
from distutils.dir_util import mkpath, copy_tree
import os
import re
import shutil

def module_directories(root):
    # find -maxdepth 1 -type d ! -name ".*"
    top, root_dirnames, _ = next(os.walk(root))
    for directory_name in root_dirnames:
        if not re.match('^\.', directory_name):
            yield directory_name

def files_for_module(module):
    # find . -maxdepth 1 -mindepth 1  -name '*.py' -not -name 'test_*' \
    #    -not -name 'setup.py'
    here, dirnames, filenames = next(os.walk(module))
    for name in filenames:
        if re.match('.+\.py$', name) \
           and not re.match('^(test_.*)|(setup\.py)$', name):
            filename = os.path.join(here, name)
            yield filename

def directories_for_module(module):
    # find . -maxdepth 1 -mindepth 1 -type d -not -name 'dist' \
    #    -not -name '*.egg-info' -not -name '__pycache__'
    here, dirnames, filenames = next(os.walk(module))
    for name in dirnames:
        if not re.match('^(dist)|(.*\.egg-info)|(__pycache__)$', name):
            dirname = os.path.join(here, name)
            yield dirname, name

def main():
    parser = argparse.ArgumentParser(
        description="Install micropython libraries",
        epilog="Omitting any MODULE installs all available modules")
    parser.add_argument(
        '-d', '--destination',
        default=os.path.join(os.environ.get('HOME'), '.micropython', 'lib'),
        help="Destination directory for library files")
    parser.add_argument('modules', metavar='MODULE', nargs='*', help="module name")
    args = parser.parse_args()
    modules = args.modules or module_directories('.')
    lib = args.destination

    mkpath(lib)
    for module in modules:
        for filename in files_for_module(module):
            shutil.copy(filename, lib)
        for dirname, name in directories_for_module(module):
            dest = os.path.join(lib, name)
            copy_tree(dirname, dest)

if __name__ == "__main__":
    main()
