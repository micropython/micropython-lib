from io import StringIO as _StringIO
from sys import stdout as _stdout


def pformat(obj, indent=1, sort_dicts=True):
    """Simply calls pprint() but capturing prints into a string and returning"""
    stream = _StringIO()
    pprint(obj, stream=stream, indent=indent, sort_dicts=sort_dicts)
    return stream.getvalue()


def pp(obj, *args, sort_dicts=False, **kwargs):
    """Same as pprint() except the default value of sort_dicts is False"""
    pprint(obj, *args, sort_dicts=sort_dicts, **kwargs)


def pprint(obj, stream=None, indent=1, sort_dicts=True):
    """Simple implementation of a pretty-printer.

    For simplicity, this does not recurse down.  It does not produce the same
    output as the CPython implementation.  Instead, it is intended to simply
    expand lists and dictionaries to multiple lines for easy viewing.
    """
    if not stream:
        stream = _stdout
    islist = isinstance(obj, list)
    isset = isinstance(obj, set)
    isdict = isinstance(obj, dict)
    if (islist or isset or isdict) and len(obj) > 1:
        print("[" if islist else "{", end="", file=stream)
        print(" " * (indent - 1), end="", file=stream)
        items = obj
        if isdict:
            items = obj.items()
            if sort_dicts:
                items = sorted(items, key=lambda x: x[0])
        first = True
        for i in items:
            if not first:
                print(",\n" + " " * indent, end="", file=stream)
            first = False
            print(f"{repr(i[0])}: {repr(i[1])}" if isdict else repr(i), end="", file=stream)
        print("]" if islist else "}", file=stream)
    else:
        # for non-builtin types or builtin types with only one element, just
        # print
        print(repr(obj), file=stream)


def ppdir(obj, *args, hidden=False, **kwargs):
    """Like calling pprint(dir(obj))

    This method is for listing the available attributes and methods of an
    object.  The main difference is that you can hide elements that start with
    an underscore by specifying hidden=False, which is the default.

    Additional arguments are forwarded on to pprint().
    """
    pprint([x for x in dir(obj) if not x.startswith("_")], *args, **kwargs)
