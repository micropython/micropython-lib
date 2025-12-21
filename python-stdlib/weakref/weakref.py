"""
# weakref
https://docs.python.org/3/library/weakref.html

Micropython does not have support for weakref in the VM, so currently this is a simple stub
module that directly assigns the object reference to simplify porting of other libraries.
"""


def ref(obj):
    return lambda: obj
