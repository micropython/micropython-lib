## CPython Standard Library

The packages in this directory aim to provide compatible implementations of
modules from the Python Standard Library, with the goal of allowing existing
Python code to run un-modified on MicroPython.

### Implementation

Many packages are implemented in pure Python, often based on the original
CPython implementation. (e.g. `collections.defaultdict`)

Some packages are based on or extend from the built-in "micro" modules in the
MicroPython firmware, providing additional functionality that didn't need to
be written in C (e.g. `collections`, `socket`, `struct`).

### Future plans (ideas for contributors):

* Add README.md to each library explaining compatibility and limitations.
