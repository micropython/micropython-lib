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

To use a unix-specific library, a manifest file must add the `unix-ffi`
library to the library search path using `add_library()`:

```py
add_library("unix-ffi", "$(MPY_LIB_DIR)/unix-ffi", prepend=True)
```

Prepending the `unix-ffi` library to the path will make it so that the
`unix-ffi` version of a package will be preferred if that package appears in
both `unix-ffi` and another library (eg `python-stdlib`).
