import glob

TEMPLATE = """\
import sys
# Remove current dir from sys.path, otherwise setuptools will peek up our
# module instead of system.
sys.path.pop(0)
from setuptools import setup


setup(name='micropython-%(name)s',
      version='%(version)s',
      description=%(desc)r,
      long_description=%(long_desc)r,
      url='https://github.com/micropython/micropython/issues/405',
      author=%(author)r,
      author_email=%(author_email)r,
      maintainer=%(maintainer)r,
      maintainer_email='micro-python@googlegroups.com',
      license=%(license)r,
      %(_what_)s=['%(top_name)s']%(_inst_req_)s)
"""

DUMMY_DESC = """\
This is a dummy implementation of a module for MicroPython standard library.
It contains zero or very little functionality, and primarily intended to
avoid import errors (using idea that even if an application imports a
module, it may be not using it onevery code path, so may work at least
partially). It is expected that more complete implementation of the module
will be provided later. Please help with the development if you are
interested in this module."""

CPYTHON_DESC = """\
This is a module ported from CPython standard library to be compatible with
MicroPython interpreter. Usually, this means applying small patches for
features not supported (yet, or at all) in MicroPython. Sometimes, heavier
changes are required. Note that CPython modules are written with availability
of vast resources in mind, and may not work for MicroPython ports with
limited heap. If you are affected by such a case, please help reimplement
the module from scratch."""

MICROPYTHON_LIB_DESC = """\
This is a module reimplemented specifically for MicroPython standard library,
with efficient and lean design in mind. Note that this module is likely work
in progress and likely supports just a subset of CPython's corresponding
module. Please help with the development if you are interested in this
module."""

MICROPYTHON_DEVELS = 'MicroPython Developers'
MICROPYTHON_DEVELS_EMAIL = 'micro-python@googlegroups.com'
CPYTHON_DEVELS = 'CPython Developers'
CPYTHON_DEVELS_EMAIL = 'python-dev@python.org'

def parse_metadata(f):
    data = {}
    for l in f:
        l = l.strip()
        k, v = l.split("=", 1)
        data[k.strip()] = v.strip()
    return data


def write_setup(fname, substs):
    with open(fname, "w") as f:
        f.write(TEMPLATE % substs)


def main():
    for fname in glob.iglob("*/metadata.txt"):
        print(fname)
        with open(fname) as f:
            data = parse_metadata(f)

        module = fname.split("/")[0]
        if data["type"] == "module":
            data["_what_"] = "py_modules"
        elif data["type"] == "package":
            data["_what_"] = "packages"
        else:
            raise ValueError

        if data["srctype"] == "dummy":
            data["author"] = MICROPYTHON_DEVELS
            data["author_email"] = MICROPYTHON_DEVELS_EMAIL
            data["maintainer"] = MICROPYTHON_DEVELS
            data["license"] = "MIT"
            data["desc"] = "Dummy %s module for MicroPython" % module
            data["long_desc"] = DUMMY_DESC
        elif data["srctype"] == "cpython":
            data["author"] = CPYTHON_DEVELS
            data["author_email"] = CPYTHON_DEVELS_EMAIL
            data["maintainer"] = MICROPYTHON_DEVELS
            data["license"] = "Python"
            data["desc"] = "CPython %s module ported to MicroPython" % module
            data["long_desc"] = CPYTHON_DESC
        elif data["srctype"] == "micropython-lib":
            if "author" not in data:
                data["author"] = MICROPYTHON_DEVELS
            if "author_email" not in data:
                data["author_email"] = MICROPYTHON_DEVELS_EMAIL
            if "maintainer" not in data:
                data["maintainer"] = MICROPYTHON_DEVELS
            if "desc" not in data:
                data["desc"] = "%s module for MicroPython" % module
            if "long_desc" not in data:
                data["long_desc"] = MICROPYTHON_LIB_DESC
            if "license" not in data:
                data["license"] = "MIT"
        else:
            raise ValueError

        data["name"] = module
        data["top_name"] = module.split(".", 1)[0]

        if "depends" in data:
            deps = ["micropython-" + x.strip() for x in data["depends"].split(",")]
            data["_inst_req_"] = ",\n      install_requires=['" + "', '".join(deps) + "']"
        else:
            data["_inst_req_"] = ""

        write_setup(module + "/setup.py", data)


if __name__ == "__main__":
    main()
