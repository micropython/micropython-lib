# Include built-in os module.
import sys

__path = sys.path
try:
    sys.path.clear()
    from os import *
finally:
    sys.path.extend(__path)

# Provide optional dependencies (which may be installed separately).
try:
    from . import path
except ImportError:
    pass

from collections import namedtuple

# https://docs.python.org/3/library/os.html#os.stat_result
stat_result = namedtuple(
    "stat_result",
    (
        "st_mode",
        "st_ino",
        "st_dev",
        "st_nlink",
        "st_uid",
        "st_gid",
        "st_size",
        "st_atime",
        "st_mtime",
        "st_ctime",
    ),
)

__os_stat = stat


def stat(path):
    return stat_result(*__os_stat(path))
