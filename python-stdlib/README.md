CPython standard libraries
==========================

The libraries in this directory aim to provide compatible implementations of
standard libraries to allow existing Python code to run un-modified on
MicroPython.

Compatibility ranges from:

 * Many commonly-used methods and classes are provided with identical runtime semantics.
 * A subset of methods and classes, with identical semantics for most use cases.
 * Additional constants not provided in the main firmware (to keep size down).
 * Stub methods and classes required to make code load without error, but may lead to runtime errors.


Implementation
--------------

Many libraries are implemented in pure Python, often based on the original
CPython implementation. (e.g. `collections.defaultdict`)

Some libraries are based on or extend from the built-in "micro" modules in the
MicroPython firmware, providing additional functionality that didn't need to
be written in C. (e.g. `socket`, `struct`)


Future plans (ideas for contributors):
--------------------------------------

* Add README.md to each library explaining compatibility and limitations.
