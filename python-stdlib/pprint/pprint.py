from io import StringIO as _StringIO
from sys import stdout as _stdout
from machine import const as _const


class PrettyPrinter:
    """A convenience class for storing pretty printer settings.

    Wraps around pformat() and pprint() calls, saving the settings for each
    call.  For parameter descriptions, look at pprint() documentation.
    """

    def __init__(self, indent=1, stream=None, sort_dicts=True):
        self.indent = indent
        self.stream = stream if stream else _stdout
        self.sort_dicts = sort_dicts

    def pformat(self, obj):
        """Call pformat() function with cached constructor values"""
        return pformat(obj, indent=self.indent, sort_dicts=self.sort_dicts)

    def pprint(self, obj):
        """Call pprint() function with cached constructor values"""
        pprint(obj, stream=self.stream, indent=self.indent, sort_dicts=self.sort_dicts)


def pformat(obj, indent=1, sort_dicts=True):
    """Simply calls pprint() but capturing prints into a string and returning.

    Does not add a newline to the end like pprint() does.
    """
    stream = _StringIO()
    _pprint_impl(obj, stream=stream, indent=indent, sort_dicts=sort_dicts)
    return stream.getvalue()


def pp(obj, *args, sort_dicts=False, **kwargs):
    """Same as pprint() except the default value of sort_dicts is False"""
    pprint(obj, *args, sort_dicts=sort_dicts, **kwargs)


def pprint(obj, stream=None, indent=1, sort_dicts=True):
    """Simple implementation of a pretty-printer.

    For simplicity, this does not recurse down.  It does not produce the same
    output as the CPython implementation.  Instead, it is intended to simply
    expand lists and dictionaries to multiple lines for easy viewing.

    Only expands containers.  Currently supported containers are set, list,
    dict, and tuple.

    stream
        The desired output stream.  If omitted (or False), the standard output
        stream will be used.

    indent
        Number of space to indent for each level of nesting.

    sort_dicts
        If true, dict keys are sorted.  You must ensure that the dicts
        encountered can be sorted against each other (for example, int cannot
        compare against a tuple, both of which can be dict keys).

    Note: raises TypeError if sort_dicts is on and sorting finds a type
    mismatch
    """
    if not stream:
        stream = _stdout
    _pprint_impl(obj, stream, indent, sort_dicts)
    stream.write("\n")  # end in a newline


def ppdir(obj, *args, hidden=False, **kwargs):
    """Like calling pprint(dir(obj))

    This method is for listing the available attributes and methods of an
    object.  The main difference is that you can hide elements that start with
    an underscore by specifying hidden=False, which is the default.

    Additional arguments are forwarded on to pprint().
    """
    pprint([x for x in dir(obj) if not x.startswith("_")], *args, **kwargs)


# Private implementation


def _pprint_impl(obj, stream, indent, sort_dicts):
    type_code = _container_type(obj)
    if type_code != _NONCONTAINER and len(obj) > 1:
        if type_code & _SIMPLE:
            _pprint_simple_container(obj, type_code, stream, indent, sort_dicts)
        else:  # type_code & _DICT:
            _pprint_dict(obj, type_code, stream, indent, sort_dicts)
    else:
        # directly print noncontainers or containers with one or fewer elements
        stream.write(repr(obj))


_NONCONTAINER = _const(0)
_SIMPLE = _const(1)
_LIST = _const(2)
_SET = _const(4)
_TUPLE = _const(8)
_DICT = _const(16)


def _container_type(obj):
    typ = type(obj)
    if issubclass(typ, list):
        return _LIST | _SIMPLE
    if issubclass(typ, set):
        return _SET | _SIMPLE
    if issubclass(typ, dict):
        return _DICT
    if issubclass(typ, tuple):
        return _TUPLE | _SIMPLE
    return _NONCONTAINER


def _pprint_simple_container(obj, type_code, stream, indent, sort_dicts):
    if type_code & _LIST:
        chars = "[]"
    elif type_code & _TUPLE:
        chars = "()"
    else:  # type_code & _SET:
        chars = "{}"

    stream.write(chars[0] + " " * (indent - 1))
    first = True
    for item in obj:
        if not first:
            stream.write(",\n" + " " * indent)
        first = False
        # TODO: would recurse here
        stream.write(repr(item))
    stream.write(chars[1])


def _pprint_dict(obj, type_code, stream, indent, sort_dicts):
    stream.write("{" + " " * (indent - 1))
    first = True
    items = obj.items()
    if sort_dicts:
        items = sorted(items, key=lambda x: x[0])
    for key, val in items:
        if not first:
            stream.write(",\n" + " " * indent)
        first = False
        # TODO: would recurse here
        stream.write(repr(key))
        stream.write(": ")
        stream.write(repr(val))
    stream.write("}")
