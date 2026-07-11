# MicroPython package installer command line
# MIT license
# Copyright (c) 2023 Jonas Scharpf (brainelectronics)

from argparse import ArgumentParser
import sys


def do_install():
    parser = ArgumentParser()
    parser.add_argument(
        "-t",
        "--target",
        help="Directory to install package",
    )
    parser.add_argument(
        "-i",
        "--index",
        help="Python Package Index, defaults to 'https://pypi.org/pypi'",
    )
    parser.add_argument(
        "--version",
        help="Specific package version, defaults to latest available",
    )
    parser.add_argument("package", nargs="+")
    args = parser.parse_args(args=sys.argv[2:])

    from . import install

    for package in args.package:
        version = None
        if "==" in package:
            package, version = package.split("==")
        install(package=package, index=args.index, target=args.target, version=version)


if len(sys.argv) >= 2:
    if sys.argv[1] == "install":
        do_install()
    else:
        print('upip: Unknown command "{}"'.format(sys.argv[1]))
