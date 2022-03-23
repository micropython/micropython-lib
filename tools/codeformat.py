#!/usr/bin/env python3
#
# This file is part of the MicroPython project, http://micropython.org/
#
# The MIT License (MIT)
#
# Copyright (c) 2020 Damien P. George
# Copyright (c) 2020 Jim Mussared
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

import argparse
import glob
import itertools
import os
import re
import subprocess

# Relative to top-level repo dir.
PATHS = [
    # C
    "**/*.[ch]",
    # Python
    "**/*.py",
]

EXCLUSIONS = []

# Path to repo top-level dir.
TOP = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

UNCRUSTIFY_CFG = os.path.join(TOP, "tools/uncrustify.cfg")

C_EXTS = (
    ".c",
    ".h",
)
PY_EXTS = (".py",)


MAIN_BRANCH = "master"
BASE_BRANCH = os.environ.get("GITHUB_BASE_REF", MAIN_BRANCH)


def list_files(paths, exclusions=None, prefix=""):
    files = set()
    for pattern in paths:
        files.update(glob.glob(os.path.join(prefix, pattern), recursive=True))
    for pattern in exclusions or []:
        files.difference_update(glob.fnmatch.filter(files, os.path.join(prefix, pattern)))
    return sorted(files)


def fixup_c(filename):
    # Read file.
    with open(filename) as f:
        lines = f.readlines()

    # Write out file with fixups.
    with open(filename, "w", newline="") as f:
        dedent_stack = []
        while lines:
            # Get next line.
            l = lines.pop(0)

            # Dedent #'s to match indent of following line (not previous line).
            m = re.match(r"( +)#(if |ifdef |ifndef |elif |else|endif)", l)
            if m:
                indent = len(m.group(1))
                directive = m.group(2)
                if directive in ("if ", "ifdef ", "ifndef "):
                    l_next = lines[0]
                    indent_next = len(re.match(r"( *)", l_next).group(1))
                    if indent - 4 == indent_next and re.match(r" +(} else |case )", l_next):
                        # This #-line (and all associated ones) needs dedenting by 4 spaces.
                        l = l[4:]
                        dedent_stack.append(indent - 4)
                    else:
                        # This #-line does not need dedenting.
                        dedent_stack.append(-1)
                else:
                    if dedent_stack[-1] >= 0:
                        # This associated #-line needs dedenting to match the #if.
                        indent_diff = indent - dedent_stack[-1]
                        assert indent_diff >= 0
                        l = l[indent_diff:]
                    if directive == "endif":
                        dedent_stack.pop()

            # Write out line.
            f.write(l)

        assert not dedent_stack, filename


def query_git_files(verbose):
    def cmd_result_set(cmd):
        ret = subprocess.run(cmd, capture_output=True).stdout.strip().decode()
        if not ret:
            return set()
        return {f.strip() for f in ret.split("\n")}

    def rel_paths(files, root):
        return {os.path.relpath(os.path.join(root, f.strip()), ".") for f in files}

    try:
        ret = set()

        # get path to root of repository
        root_dir = (
            subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True)
            .stdout.strip()
            .decode()
        )

        # Check locally modified files
        status = cmd_result_set(["git", "status", "--porcelain"])
        dirty_files = rel_paths({line.split(" ", 1)[-1] for line in status}, root_dir)
        ret |= dirty_files

        # Current commit and branch
        current_commit = (
            subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True)
            .stdout.strip()
            .decode()
        )
        current_branches = cmd_result_set(["git", "branch", "--contains", current_commit])
        if MAIN_BRANCH in current_branches:
            if ret:
                if verbose:
                    print("Local changes detected, only scanning them.")
                return ret

            # We're on clean master, run on entire repo
            if verbose:
                print("Scanning whole repository")
            return None

        # List the files modified on current branch
        if verbose:
            print("Scanning changes from current branch and any local changes")
        files_on_branch = rel_paths(
            cmd_result_set(["git", "diff", "--name-only", BASE_BRANCH]), root_dir
        )
        ret |= files_on_branch
        return ret
    except:
        # Git not available, run on entire repo
        return None


def main():
    cmd_parser = argparse.ArgumentParser(description="Auto-format C and Python files.")
    cmd_parser.add_argument("-c", action="store_true", help="Format C code only")
    cmd_parser.add_argument("-p", action="store_true", help="Format Python code only")
    cmd_parser.add_argument("-v", action="store_true", help="Enable verbose output")
    cmd_parser.add_argument(
        "files",
        nargs="*",
        help="Run on specific globs. If not specied current branch changes will be used",
    )
    args = cmd_parser.parse_args()

    # Setting only one of -c or -p disables the other. If both or neither are set, then do both.
    format_c = args.c or not args.p
    format_py = args.p or not args.c

    # Expand the globs passed on the command line, or use the default globs above.
    files = []
    if args.files:
        files = list_files(args.files)
    else:
        files = query_git_files(verbose=args.v)
        if not files:
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

    # Format C files with uncrustify.
    if format_c:
        command = ["uncrustify", "-c", UNCRUSTIFY_CFG, "-lC", "--no-backup"]
        if not args.v:
            command.append("-q")
        batch(command, lang_files(C_EXTS))
        for file in lang_files(C_EXTS):
            fixup_c(file)

    # Format Python files with black.
    if format_py:
        command = ["black", "--fast", "--line-length=99"]
        if args.v:
            command.append("-v")
        else:
            command.append("-q")
        batch(command, lang_files(PY_EXTS))


if __name__ == "__main__":
    main()
