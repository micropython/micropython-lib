micropython-lib
===============
micropython-lib is a project to develop a non-monolothic standard library
for MicroPython (https://github.com/micropython/micropython). Each module
or package is available as a separate distribution package from PyPI. Each
module is either written from scratch or ported from CPython.

Note that the main target of micropython-lib is a "Unix" port of MicroPython.
Actual system requirements vary per module. Though if a module is not related
to I/O, the module should work without problems on bare-metal ports too (e.g.
pyboard).


Usage
-----
micropython-lib packages are published on PyPI (Python Package Index),
the standard Python community package repository: http://pypi.python.org/ .
On PyPI, you can search for MicroPython related packages and read
additional package information. By convention, all micropython-lib package
names are prefixed with "micropython-".
Browse available packages
[via this URL](https://pypi.python.org/pypi?%3Aaction=search&term=micropython).
(Note: search results may include both micropython-lib and 3rd-party
packages).

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

Note on OSX
-
By default OSX uses the BSD versions of basic core utilities. The
micropython-lib `Makefile` make use of certain GNU-specific options
for some of these utilities (`find`, `xargs`, and `cp`)
This is being tracked at https://github.com/micropython/micropython-lib/issues/10
Until the Makefile is revised to work on both GNU and BSD based
systems, the following workaround is available for OSX users:
 * Use Macports to install the GNU coreutils:
`sudo port install coreutils`
 * Make a copy of `Makefile`, naming it something like `Makefile-osx`,
and modify this copy of the Makefile to use the GNU versions of the
utilities you just installed: change `find` to `gfind`, `xargs` to
`gxargs`, and `cp` to `gcp`
 * Now run `gmake --makefile=Makefile-osx install` to install
micropython-lib to its default location (`~/.micropython/lib`) 


Links
-----
If you would like to trace evolution of MicroPython packaging support,
you may find following links useful (note that they may contain outdated
information):

 * https://github.com/micropython/micropython/issues/405
 * http://forum.micropython.org/viewtopic.php?f=5&t=70

Guidelines for packaging MicroPython modules for PyPI:

 * https://github.com/micropython/micropython/issues/413
