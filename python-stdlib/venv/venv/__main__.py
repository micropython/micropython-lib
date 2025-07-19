# Support for creating MicroPython virtual environments using `micropython -m venv`
# MIT license; Copyright (c) 2022 Jim Mussared

import argparse
import os
import sys


# If mip is not frozen into this binary, then also install it in the venv.
def install_mip(venv_lib_path):
    need_mip = False
    if "mip" in sys.modules:
        del sys.modules["mip"]
    saved_sys_path = sys.path[:]
    try:
        sys.path[:] = [".frozen"]
        try:
            import mip

            print("mip is frozen")
        except ImportError:
            need_mip = True
    finally:
        sys.path[:] = saved_sys_path

    if need_mip:
        import mip

        mip.install("mip-cmdline", target=venv_lib_path)


def do_venv():
    parser = argparse.ArgumentParser(description="Create a micropython virtual environment")
    parser.add_argument("path", nargs=1, help="Path to create the virtual environment in")
    args = parser.parse_args(args=sys.argv[1:])
    venv_path = args.path[0]
    print("Creating virtual environment in:", venv_path)

    # Equivalent to path = os.abspath(path).
    if not venv_path.startswith("/"):
        venv_path = os.getcwd() + os.sep + venv_path

    venv_bin_path = venv_path + os.sep + "bin"
    venv_lib_path = venv_path + os.sep + "lib"

    for d in (
        venv_path,
        venv_bin_path,
        venv_lib_path,
    ):
        try:
            os.mkdir(d)
        except:
            pass

    # Note the venv/lib dir goes before .frozen so that installed packages replace frozen ones.
    with open(venv_bin_path + os.sep + "activate", "w") as f:
        print(
            """# Usage: source bin/activate

deactivate() {{
    PATH="$_OLD_VIRTUAL_PATH"
    export PATH

    MICROPYPATH="$_OLD_VIRTUAL_MICROPYPATH"
    if [ -z "$MICROPYPATH" ]; then
        export -n MICROPYPATH
    else
        export MICROPYPATH
    fi

    unset VIRTUAL_ENV

    unset deactivate
}}

VIRTUAL_ENV={}

_OLD_VIRTUAL_PATH="$PATH"
PATH="$VIRTUAL_ENV/bin:$PATH"
export PATH

_OLD_VIRTUAL_MICROPYPATH="$MICROPYPATH"
MICROPYPATH="$VIRTUAL_ENV/lib:.frozen"
export MICROPYPATH
""".format(
                venv_path
            ),
            file=f,
        )

    # Add a `micropython` binary in $PATH pointing to this binary.
    if hasattr(sys, "executable"):
        os.system("cp {} {}".format(sys.executable, venv_bin_path + os.sep + "micropython"))

    install_mip(venv_lib_path)


do_venv()
