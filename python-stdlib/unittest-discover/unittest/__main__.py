# Extension for "unittest" that adds the ability to run via "micropython -m unittest".

import argparse
import os
import sys
from fnmatch import fnmatch
from micropython import const

try:
    from unittest import TestRunner, TestResult, TestSuite
except ImportError:
    print("Error: This must be used from an installed copy of unittest-discover which will"
          " also install base unittest module.")
    raise


# Run a single test in a clean environment.
def _run_test_module(runner: TestRunner, module_name: str, *extra_paths: list[str]):
    module_snapshot = {k: v for k, v in sys.modules.items()}
    path_snapshot = sys.path[:]
    try:
        for path in extra_paths:
            if path:
                sys.path.insert(0, path)

        module = __import__(module_name, None, None, module_name)
        suite = TestSuite(module_name)
        suite._load_module(module)
        return runner.run(suite)
    finally:
        sys.path[:] = path_snapshot
        sys.modules.clear()
        sys.modules.update(module_snapshot)


_DIR_TYPE = const(0x4000)


def _run_all_in_dir(runner: TestRunner, path: str, pattern: str, top: str):
    result = TestResult()
    for fname, ftype, *_ in os.ilistdir(path):
        if fname in ("..", "."):
            continue
        fpath = "/".join((path, fname))
        if ftype == _DIR_TYPE:
            result += _run_all_in_dir(
                runner=runner,
                path=fpath,
                pattern=pattern,
                top=top,
            )
        if fnmatch(fname, pattern):
            module_path = fpath.rsplit(".", 1)[0]  # remove ext
            module_path = module_path.replace("/", ".").strip(".")
            result += _run_test_module(runner, module_path, top)
    return result


# Implements discovery inspired by https://docs.python.org/3/library/unittest.html#test-discovery
def _discover(runner: TestRunner):
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

    return _run_all_in_dir(
        runner=runner,
        path=path,
        pattern=args.pattern,
        top=top,
    )


# TODO: Use os.path for path handling.
PATH_SEP = getattr(os, "sep", "/")


# foo/bar/x.y.z --> foo/bar, x.y
def _dirname_filename_no_ext(path):
    # Workaround: The Windows port currently reports "/" for os.sep
    # (and MicroPython doesn't have os.altsep). So for now just
    # always work with os.sep (i.e. "/").
    path = path.replace("\\", PATH_SEP)

    split = path.rsplit(PATH_SEP, 1)
    if len(split) == 1:
        dirname, filename = "", split[0]
    else:
        dirname, filename = split
    return dirname, filename.rsplit(".", 1)[0]


def discover_main():
    runner = TestRunner()

    if len(sys.argv) == 1 or (
        len(sys.argv) >= 2
        and _dirname_filename_no_ext(sys.argv[0])[1] == "unittest"
        and sys.argv[1] == "discover"
    ):
        # No args, or `python -m unittest discover ...`.
        result = _discover(runner)
    else:
        result = TestResult()
        for test_spec in sys.argv[1:]:
            try:
                os.stat(test_spec)
                # File exists, strip extension and import with its parent directory in sys.path.
                dirname, module_name = _dirname_filename_no_ext(test_spec)
                res = _run_test_module(runner, module_name, dirname)
            except OSError:
                # Not a file, treat as named module to import.
                res = _run_test_module(runner, test_spec)

            result += res

    if not result.testsRun:
        # If tests are run their results are already printed.
        # Ensure an appropriate output is printed if no tests are found.
        runner.run(TestSuite())

    # Terminate with non zero return code in case of failures.
    sys.exit(result.failuresNum + result.errorsNum)


discover_main()
