"""
# weakref
https://docs.python.org/3/library/weakref.html

The weakref module allows the Python programmer to create weak references to objects.
In the following, the term referent means the object which is referred to by a weak reference.
A weak reference to an object is not enough to keep the object alive: when the only remaining references to a referent are weak references, garbage collection is free to destroy the referent and reuse its memory for something else. However, until the object is actually destroyed the weak reference may return the object even if there are no strong references to it.
A primary use for weak references is to implement caches or mappings holding large objects, where it’s desired that a large object not be kept alive solely because it appears in a cache or mapping.

Micropython does not have support for weakref in the VM, so currently this is a simple stub
module that directly assigns the object reference to simplify porting of other libraries.
"""


def ref(obj):
    return lambda: obj
