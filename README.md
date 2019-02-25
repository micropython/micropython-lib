micropython-lib
===============
micropython-lib is a project to develop a non-monolothic standard library
for "advanced" MicroPython fork (https://github.com/pfalcon/micropython).
Each module or package is available as a separate distribution package from
PyPI. Each module comes from one of the following sources (and thus each
module has its own licensing terms):

* written from scratch specifically for MicroPython
* ported from CPython
* ported from some other Python implementation, e.g. PyPy
* some modules actually aren't implemented yet and are dummy

Note that the main target of micropython-lib is a "Unix" port of the
aforementioned fork of MicroPython. Actual system requirements vary per
module. Majority of modules are compatible with the upstream MicroPython,
though some may require additional functionality/optimizations present in
the "advanced" fork. Modules not related to I/O may also work without
problems on bare-metal ports, not just on "Unix" port (e.g. pyboard).


Usage
-----
micropython-lib packages are published on PyPI (Python Package Index),
the standard Python community package repository: https://pypi.org/ .
On PyPI, you can search for MicroPython related packages and read
additional package information. By convention, all micropython-lib package
names are prefixed with "micropython-" (the reverse is not true - some
package starting with "micropython-" aren't part of micropython-lib and
were released by 3rd parties).

Browse available packages [via this
URL](https://pypi.org/search/?q=&o=&c=Programming+Language+%3A%3A+Python+%3A%3A+Implementation+%3A%3A+MicroPython).

To install packages from PyPI for usage on your local system, use the
`upip` tool, which is MicroPython's native package manager, similar to
`pip`, which is used to install packages for CPython. `upip` is bundled
with MicroPython "Unix" port (i.e. if you build "Unix" port, you
automatically have `upip` tool). Following examples assume that
`micropython` binary is available on your `PATH`:

~~~~
$ micropython -m upip install micropython-pystone
...
$ micropython
>>> import pystone
>>> pystone.main()
Pystone(1.2) time for 50000 passes = 0.534
This machine benchmarks at 93633 pystones/second
~~~~

Run `micropython -m upip --help` for more information about `upip`.


Development
-----------
To install modules during development, use `make install`. By default, all
available packages will be installed. To install a specific module, add the
`MOD=<module>` parameter to the end of the `make install` command.


Links
-----
If you would like to trace evolution of MicroPython packaging support,
you may find following links useful (note that they may contain outdated
information):

 * https://github.com/micropython/micropython/issues/405
 * http://forum.micropython.org/viewtopic.php?f=5&t=70

Guidelines for packaging MicroPython modules for PyPI:

 * https://github.com/micropython/micropython/issues/413
