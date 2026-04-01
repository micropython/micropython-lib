# copy

Non-trivial objects (eg. classes) instantiated by CPython are usually able to
be copied by methods of this module without any modification, as the copying
mechanism makes use of two functions (`__reduce__` and `__reduce_ex__`) that
are added to instances by CPython itself.

MicroPython does not do that, to keep the interpreter's binary size down and to
limit the RAM footprint of object instances.  This means that this module is
not able to copy non-trivial objects without specific changes to your code.

The `copy` module methods look for two methods being available in an instance:
[`__copy__`](https://docs.python.org/3/library/copy.html#object.__copy__) and
[`__deepcopy__`](https://docs.python.org/3/library/copy.html#object.__deepcopy__),
and the module will call those functions to create a copy (either shallow or
deep) of the object.  Implementing either of those methods in a class will
allow instances of that class to be copied both in MicroPython and CPython,
keeping code compatible with the two interpreters.

`__reduce__` and `__reduce_ex__` will be used in MicroPython if a class
provides them, but unless you're also planning to use object pickling,
`__copy__` and `__deepcopy__` are the simplest way to make sure things work in
all cases.
