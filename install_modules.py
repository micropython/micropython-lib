#!/usr/bin/env python3

# Install micropython modules

from distutils.dir_util import mkpath, copy_tree
import os
import re
import shutil
import sys

def install(modules, lib):
    mkpath(lib)
    for module in modules:
        install_from_module(module, lib)

def module_directories(root):
    # find -maxdepth 1 -type d ! -name ".*"
    top, root_dirnames, _ = os.walk(root).send(None)
    for directory_name in root_dirnames:
        if not re.match('^\.', directory_name):
            yield directory_name

def install_from_module(module, lib):
    for filename in files_for_module(module):
        print("shutil.copy(%s, %s)" % (filename, lib))
        shutil.copy(filename, lib)
    for dirname, name in directories_for_module(module):
        dest = os.path.join(lib, name)
        print("copy_tree(%s, %s)" % (dirname, dest))
        copy_tree(dirname, dest)


def files_for_module(module):
    # find . -maxdepth 1 -mindepth 1  -name '*.py' -not -name 'test_*' \
    #    -not -name 'setup.py'
    here, dirnames, filenames = os.walk(module).send(None)
    for name in filenames:
        if re.match('.+\.py$', name) \
           and not re.match('^(test_.*)|(setup\.py)$', name):
            filename = os.path.join(here, name)
            yield filename

def directories_for_module(module):
    # find . -maxdepth 1 -mindepth 1 -type d -not -name 'dist' \
    #    -not -name '*.egg-info' -not -name '__pycache__'
    here, dirnames, filenames = os.walk(module).send(None)
    for name in dirnames:
        if not re.match('^(dist)|(.*\.egg-info)|(__pycache__)$', name):
            dirname = os.path.join(here, name)
            yield dirname, name

def main(argv):
    lib = os.path.join(os.environ.get('HOME'), \
                                    '.micropython', 'lib')
    if len(argv) > 1 and re.match('^(-h)|(--help)', argv[1]):
        print(
"""Usage: %s [MODULE_NAME]...
Install micropython library modules in %s
Omitting any MODULE_NAMEs will install them all.""" \
              % (argv[0], lib))
        sys.exit(0)
    command_line_modules = argv[1:]
    modules = command_line_modules or module_directories('.')
    install(modules, lib)

if __name__ == "__main__":
    main(sys.argv)
