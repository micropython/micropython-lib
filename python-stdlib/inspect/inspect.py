import sys

# Generator function.
_g = lambda: (yield)

# Closure type.
_ct = type((lambda x: (lambda: x))(None))

def getmembers(obj, pred=None):
    res = []
    for name in dir(obj):
        val = getattr(obj, name)
        if pred is None or pred(val):
            res.append((name, val))
    res.sort()
    return res


def isfunction(obj):
    return isinstance(obj, type(isfunction))


def isgeneratorfunction(obj):
    return isinstance(obj, type(_g))


def isgenerator(obj):
    return isinstance(obj, type((_g)()))


# In MicroPython there's currently no way to distinguish between generators and coroutines.
iscoroutinefunction = isgeneratorfunction
iscoroutine = isgenerator


class _Class:
    def meth():
        pass


_Instance = _Class()


def ismethod(obj):
    return isinstance(obj, type(_Instance.meth))


def isclass(obj):
    return isinstance(obj, type)


def ismodule(obj):
    return isinstance(obj, type(sys))


def getargspec(func):
    raise NotImplementedError("This is over-dynamic function, not supported by MicroPython")


def getmodule(obj, _filename=None):
    return None  # Not known


def getmro(cls):
    return [cls]


def getsourcefile(obj):
    return None  # Not known


def getfile(obj):
    return "<unknown>"


def getsource(obj):
    return "<source redacted to save you memory>"


def currentframe():
    return None


def getframeinfo(frame, context=1):
    return ("<unknown>", -1, "<unknown>", [""], 0)


class Signature:
    pass


# This `signature()` function is very limited.  It's main purpose is to work out
# the arity of the given function, ie the number of arguments it takes.
#
# The return value is an instance of `Signature` with a `parameters` member which
# is an OrderedDict whose length is the number of arguments of `f`.
def signature(f):
    import collections
    import uctypes

    s = Signature()
    s.parameters = collections.OrderedDict()

    t = type(f)
    if t is type(globals):
        # A zero-parameter built-in.
        num_args = 0
    elif t is type(abs):
        # A one-parameter built-in.
        num_args = 1
    elif t is type(hasattr):
        # A two-parameter built-in.
        num_args = 2
    elif t is type(setattr):
        # A three-parameter built-in.
        num_args = 3
    elif t is type(signature) or t is type(_g) or t is _ct:
        # A bytecode function, work out the number of arguments by inspecting the bytecode data.
        fun_ptr = id(f)
        num_closed_over = 0
        if t is _ct:
            # A closure, the function is the second word.
            clo_ptr = uctypes.struct(fun_ptr, (uctypes.ARRAY | 0, uctypes.LONG | 3))
            fun_ptr = clo_ptr[1]
            num_closed_over = clo_ptr[2]
        fun_obj = uctypes.struct(fun_ptr, (uctypes.ARRAY | 0, uctypes.LONG | 4))
        bytecode = uctypes.bytearray_at(fun_obj[3], 8)
        # See py/bc.h:MP_BC_PRELUDE_SIG_DECODE_INTO macro.
        i = 0
        z = bytecode[i]
        i += 1
        A = z & 0x3
        K = 0
        n = 0
        while z & 0x80:
            z = bytecode[i]
            i += 1
            A |= (z & 0x4) << n
            K |= ((z & 0x08) >> 3) << n
        num_args = A + K - num_closed_over
    else:
        raise NotImplementedError("unsupported function type")

    # Add dummy arguments to the OrderedDict.
    for i in range(num_args):
        a = "x{}".format(i)
        s.parameters[a] = a

    return s
