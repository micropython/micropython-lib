#!/usr/bin/env python3
#
# This file is part of the MicroPython project, http://micropython.org/
#
# The MIT License (MIT)
#
# Copyright (c) 2020 Damien P. George
# Copyright (c) 2023 Jim Mussared
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

# This is based on tools/codeformat.py from the main micropython/micropython
# repository but without support for .c/.h files.

import argparse
import glob
import itertools
import os
import re
import subprocess

# Relative to top-level repo dir.
PATHS = [
    "**/*.py",
]

EXCLUSIONS = []

# Path to repo top-level dir.
TOP = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

PY_EXTS = (".py",)


def list_files(paths, exclusions=None, prefix=""):
    files = set()
    for pattern in paths:
        files.update(glob.glob(os.path.join(prefix, pattern), recursive=True))
    for pattern in exclusions or []:
        files.difference_update(glob.fnmatch.filter(files, os.path.join(prefix, pattern)))
    return sorted(files)


def main():
    cmd_parser = argparse.ArgumentParser(description="Auto-format Python files.")
    cmd_parser.add_argument("-v", action="store_true", help="Enable verbose output")
    cmd_parser.add_argument(
        "-f",
        action="store_true",
        help="Filter files provided on the command line against the default list of files to check.",
    )
    cmd_parser.add_argument("files", nargs="*", help="Run on specific globs")
    args = cmd_parser.parse_args()

    # Expand the globs passed on the command line, or use the default globs above.
    files = []
    if args.files:
        files = list_files(args.files)
        if args.f:
            # Filter against the default list of files. This is a little fiddly
            # because we need to apply both the inclusion globs given in PATHS
            # as well as the EXCLUSIONS, and use absolute paths
            files = {os.path.abspath(f) for f in files}
            all_files = set(list_files(PATHS, EXCLUSIONS, TOP))
            if args.v:  # In verbose mode, log any files we're skipping
                for f in files - all_files:
                    print("Not checking: {}".format(f))
            files = list(files & all_files)
    else:
        files = list_files(PATHS, EXCLUSIONS, TOP)

    # Extract files matching a specific language.
    def lang_files(exts):
        for file in files:
            if os.path.splitext(file)[1].lower() in exts:
                yield file

    # Run tool on N files at a time (to avoid making the command line too long).
    def batch(cmd, files, N=200):
        while True:
            file_args = list(itertools.islice(files, N))
            if not file_args:
                break
            subprocess.check_call(cmd + file_args)

    # Format Python files with black.
    command = ["black", "--fast", "--line-length=99"]
    if args.v:
        command.append("-v")
    else:
        command.append("-q")
    batch(command, lang_files(PY_EXTS))


if __name__ == "__main__":
    main()
