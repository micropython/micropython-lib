~~~~
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
micropython-lib is a highly experimental community project.

Please help to drive it to just "experimental" state by testing
provided packages with MicroPython.
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
~~~~

micropython-lib
===============
micropython-lib is a project to develop a non-monolothic standard library
for MicroPython. Each module or package is available as a separate
distribution package from PyPI. Each module is either written from scratch or
ported from CPython. 

Note that the main target of micropython-lib is a "Unix" port of MicroPython
(future ports to be determined). Actual system requirements vary per module.
Though if a module is not related to I/O, the module should work without
problem on bare-metal ports too.


Usage
-----
micropython-lib packages are published on PyPI (Python Package Index),
the standard Python community package repository: http://pypi.python.org/ .
On PyPi, you can search for MicroPython related packages and read
additional package information.

To install packages from PyPI for usage on your local system, use the
`pip-micropython` tool, which is a simple wrapper around the standard
`pip` tool, which is used to install packages for CPython.
The `pip-micropython` tool can be found in `tools` subdirectory 
of the main MicroPython repository (https://github.com/micropython/micropython).
Just install the `pip-micropython` script somewhere on your `PATH`.

Afterwards, just use `pip-micropython` in a way similar to `pip`:

~~~~
$ pip-micropython install micropython-copy
$ micropython
>>> import copy
>>> copy.copy([1, 2, 3])
[1, 2, 3]
~~~~

Review the `pip-micropython` source code for more info.


Development
-----------
To install modules during development, use `make install`. By default, all
available packages will be installed. To install a specific module, add the 
`MOD=<module>` parameter to the end of the `make install` command.


Links
-----
More information is on GitHub and in the MicroPython forums:

 * https://github.com/micropython/micropython/issues/405
 * http://forum.micropython.org/viewtopic.php?f=5&t=70

For basic guidelines for installing packages from PyPI:

 * https://github.com/micropython/micropython/issues/413
