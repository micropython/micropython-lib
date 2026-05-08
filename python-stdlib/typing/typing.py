"""
This module provides runtime support for type hints.
based on : 
- https://github.com/micropython/micropython-lib/pull/584
- https://github.com/Josverl/micropython-stubs/tree/main/mip
- https://github.com/Josverl/rt_typing

"""

# -------------------------------------
# code reduction by Ignoring type hints
# -------------------------------------
class __Ignore:
    """A class to ignore type hints in code."""

    def __call__(*args, **kwargs):
        # May need some guardrails here
        pass

    def __getitem__(self, arg):
        # May need some guardrails here
        return __ignore

    def __getattr__(self, attr):
        if attr in self.__dict__:
            return self.__dict__[attr]
        return __ignore


__ignore = __Ignore()
# -----------------
# typing essentials
# -----------------
TYPE_CHECKING = False

def final(arg):  # ( 6 +  bytes)
    # decorator to indicate that a method should not be overridden
    # https://docs.python.org/3/library/typing.html#typing.final
    return arg


# def overload(arg):  # ( 27 bytes)
#     # ignore functions signatures with @overload decorator
#     return None
overload = __ignore # saves bytes, and is semantically similar

def NewType(_, arg):  # (21 bytes)
    # https://docs.python.org/3/library/typing.html#newtype
    # MicroPython: just use the original type.
    return arg

# ---------------
#  useful methods
# ---------------

# https://docs.python.org/3/library/typing.html#typing.cast
# def cast(type, arg):  # ( 23 bytes)
#     return arg
cast = NewType # saves bytes, and is semantically similar

# https://docs.python.org/3/library/typing.html#typing.no_type_check
# def no_type_check(arg):  # ( 26 bytes)
#     # decorator to disable type checking on a function or method
#     return arg
no_type_check = final # saves bytes, and is semantically similar

# -------------------
# less useful methods
# -------------------

# def reveal_type(x):  # ( 38 bytes)
# #     # https://docs.python.org/3/library/typing.html#typing.reveal_type
#     return x
# or for smaller size:
reveal_type = final # saves bytes, and is semantically similar


# def get_origin(type):  # ( 23 bytes)
#     # https://docs.python.org/3/library/typing.html#typing.get_origin
#     #  Return None for all unsupported objects.
#     return None


# def get_args(arg):  # ( 22 bytes)
#     # https://docs.python.org/3/library/typing.html#typing.get_args
#     # Python 3.8+ only
#     return ()


# ref: https://github.com/micropython/micropython-lib/pull/584#issuecomment-2317690854

def __getattr__(x):
    return __ignore

# snarky way to alias typing_extensions to typing ( saving 59 bytes)
import sys
sys.modules["typing_extensions"] = sys.modules["typing"]
