import argparse
import sys
import uos
from fnmatch import fnmatch

from unittest import TestRunner, TestResult, run_module


def discover(runner: TestRunner):
    """
    Implements discover function inspired by https://docs.python.org/3/library/unittest.html#test-discovery
    """
    parser = argparse.ArgumentParser()
    # parser.add_argument(
    #     "-v",
    #     "--verbose",
    #     action="store_true",
    #     help="Verbose output",
    # )
    parser.add_argument(
        "-s",
        "--start-directory",
        dest="start",
        default=".",
        help="Directory to start discovery",
    )
    parser.add_argument(
        "-p",
        "--pattern ",
        dest="pattern",
        default="test*.py",
        help="Pattern to match test files",
    )
    parser.add_argument(
        "-t",
        "--top-level-directory",
        dest="top",
        help="Top level directory of project (defaults to start directory)",
    )
    args = parser.parse_args(args=sys.argv[2:])

    path = args.start
    top = args.top or path

    return run_all_in_dir(
        runner=runner,
        path=path,
        pattern=args.pattern,
        top=top,
    )


def run_all_in_dir(runner: TestRunner, path: str, pattern: str, top: str):
    DIR_TYPE = 0x4000

    result = TestResult()
    for fname, type, *_ in uos.ilistdir(path):
        if fname in ("..", "."):
            continue
        if type == DIR_TYPE:
            result += run_all_in_dir(
                runner=runner,
                path="/".join((path, fname)),
                pattern=pattern,
                top=top,
            )
        if fnmatch(fname, pattern):
            modname = fname[: fname.rfind(".")]
            result += run_module(runner, modname, path, top)
    return result
