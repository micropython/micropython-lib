from builtins import open as _builtin_open


def open(filename):
    """Open a file in read only text mode using utf8.
    """
    return _builtin_open(filename, "r", encoding="utf8")

