# MicroPython package installer command line
# MIT license; Copyright (c) 2022 Jim Mussared

import argparse
import sys


def do_install():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-t",
        "--target",
        help="Directory to start discovery",
    )
    parser.add_argument(
        "-i",
        "--index",
        help="Pattern to match test files",
    )
    parser.add_argument(
        "--mpy",
        action="store_true",
        help="download as compiled .mpy files (default)",
    )
    parser.add_argument(
        "--no-mpy",
        action="store_true",
        help="download as .py source files",
    )
    parser.add_argument("package", nargs="+")
    args = parser.parse_args(args=sys.argv[2:])

    from . import install

    for package in args.package:
        version = None
        if "@" in package:
            package, version = package.split("@")
        install(package, args.index, args.target, version, not args.no_mpy)


if len(sys.argv) >= 2:
    if sys.argv[1] == "install":
        do_install()
    else:
        print('mip: Unknown command "{}"'.format(sys.argv[1]))
