## Unix-specific packages

These are packages that will only run on the Unix port of MicroPython, or are
too big to be used on microcontrollers. There is some limited support for the
Windows port too.

**Note:** This directory is unmaintained.

### Background

The packages in this directory provide additional CPython compatibility using
the host operating system's native libraries.

This is implemented either by accessing the libraries directly via libffi, or
by using built-in modules that are only available on the Unix port.

In theory, this allows you to use MicroPython as a more complete drop-in
replacement for CPython.

### Usage

To use a unix-specific library, pass `unix_ffi=True` to `require()` in your
manifest file.

```py
require("os", unix_ffi=True) # Use the unix-ffi version instead of python-stdlib.
```
