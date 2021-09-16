import io as _io
import sys as _sys

try:
    from micropython import const as _const
except ImportError:
    _const = lambda x: x


class PrettyPrinter:
    """A convenience class for storing pretty printer settings.

    Wraps around pformat() and pprint() calls, saving the settings for each
    call.  For parameter descriptions, look at pprint() documentation.
    """

    def __init__(self, indent=1, depth=1, stream=None, sort_dicts=True):
        self._indent = indent
        self._depth = depth
        self._stream = stream if stream else _sys.stdout
        self._sort_dicts = sort_dicts

    def pformat(self, obj):
        """Call pformat() function with cached constructor values"""
        return pformat(obj, indent=self._indent, depth=self._depth, sort_dicts=self._sort_dicts)

    def pprint(self, obj):
        """Call pprint() function with cached constructor values"""
        pprint(
            obj,
            stream=self._stream,
            indent=self._indent,
            depth=self._depth,
            sort_dicts=self._sort_dicts,
        )


def pformat(obj, indent=1, depth=1, sort_dicts=True):
    """Simply calls pprint() but capturing prints into a string and returning.

    Does not add a newline to the end like pprint() does.
    """
    stream = _io.StringIO()
    _pprint_impl(obj, stream, 0, sort_dicts, depth, 0, indent)
    return stream.getvalue()


def pp(obj, *args, sort_dicts=False, **kwargs):
    """Same as pprint() except the default value of sort_dicts is False"""
    pprint(obj, *args, sort_dicts=sort_dicts, **kwargs)


def pprint(obj, stream=None, indent=1, depth=1, sort_dicts=True):
    """Simple implementation of a pretty-printer.

    It does not produce the same output as the CPython implementation, but it's
    close.  Instead, it is intended to simply expand lists and dictionaries to
    multiple lines for easy viewing.  When the recursion depth has been
    reached, the elements will be printed with repl(item) instead of the
    CPython implementation of eliding the results (e.g., "{...}").  This is
    because this implementation is not as safe as the CPython implementation
    for deep recursion, which is detailed two paragraphs lower.

    Only expands containers.  Currently supported containers are set, list,
    dict, and tuple.

    The depth parameter defaults to 1 which is different from the CPython
    implementation which defaults to None, meaning infinite recursion.  This
    implementation is significantly simpler and does not have safety checks
    against recursive structures (i.e., structures that contain a copy of
    themselves somewhere) or costly overexpansion.  This simplicity gains speed
    and memory efficiency at the potential cost of expanding too far.  Increase
    the depth parameter cautiously.

    stream
        The desired output stream.  If omitted (or False), the standard output
        stream will be used.

    indent
        Number of space to indent for each level of nesting.

    depth
        The maximum depth to print out nested structures.  Set to None for
        infinite depth.  Warning: be careful of infinite depth as infinite
        recursion and overexpansion checks are not performed.

    sort_dicts
        If true, dict keys are sorted.  You must ensure that the dicts
        encountered can be sorted against each other (for example, int cannot
        compare against a tuple, both of which can be dict keys).

    Note: raises TypeError if sort_dicts is on and sorting finds a type
    mismatch
    """
    if not stream:
        stream = _sys.stdout
    _pprint_impl(obj, stream, 0, sort_dicts, depth, 0, indent)
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


def _pprint_impl(obj, stream, indent, sort_dicts, maxlevel, level, indent_per_level):
    type_code = _container_type(obj)
    if (maxlevel is not None and level >= maxlevel) or type_code == _NONCONTAINER or not obj:
        # directly print noncontainers, empty containers, or if we have reached
        # the max level.
        stream.write(repr(obj))
    else:
        # expand the container
        if type_code & _SIMPLE:
            _pprint_simple_container(
                obj,
                type_code,
                stream,
                indent + indent_per_level,
                sort_dicts,
                maxlevel,
                level + 1,
                indent_per_level,
            )
        else:  # type_code & _DICT:
            _pprint_dict(
                obj,
                type_code,
                stream,
                indent + indent_per_level,
                sort_dicts,
                maxlevel,
                level + 1,
                indent_per_level,
            )


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


def _pprint_simple_container(
    obj, type_code, stream, indent, sort_dicts, maxlevel, level, indent_per_level
):
    if type_code & _LIST:
        chars = "[]"
    elif type_code & _TUPLE:
        chars = "()"
    else:  # type_code & _SET:
        chars = "{}"

    indent_string = " " * indent

    stream.write(chars[0])
    stream.write(" " * (indent_per_level - 1))
    first = True
    for item in obj:
        if not first:
            stream.write(",\n")
            stream.write(indent_string)
        first = False
        # recurse here
        _pprint_impl(item, stream, indent, sort_dicts, maxlevel, level, indent_per_level)
    if type_code & _TUPLE and len(obj) == 1:
        stream.write(",")
    stream.write(chars[1])


def _pprint_dict(obj, type_code, stream, indent, sort_dicts, maxlevel, level, indent_per_level):
    indent_string = " " * indent
    stream.write("{")
    stream.write(" " * (indent_per_level - 1))
    first = True
    items = obj.items()
    if sort_dicts:
        items = sorted(items, key=lambda x: x[0])
    for key, val in items:
        if not first:
            stream.write(",\n")
            stream.write(indent_string)
        first = False
        # python's implementation does not multiline keys, then offsets the
        # value by the key's length.  They still do safety checks such as
        # recursiveness and checking that it can be printed within the
        # specified width, which we skip in this implementation.
        keystr = repr(key)
        stream.write(keystr)
        stream.write(": ")
        # recurse on the value, lined up to wrap in front of the colon.
        _pprint_impl(
            val, stream, indent + len(keystr) + 2, sort_dicts, maxlevel, level, indent_per_level
        )
    stream.write("}")
