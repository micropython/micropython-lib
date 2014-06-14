~~~~
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
micropython-lib is highly experimental community project.

Please help to drive it to just "expiremental" state by testing
provided packages with MicroPython.
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
~~~~

micropython-lib
===============
micropython-lib is a project to develop non-monolothic standard library
for MicroPython. Each module or package is available as a seprate
distribution package from PyPI. Modules either written from scratch or
ported from CPython. Note that main target of micropython-lib is so
far "Unix" port of MicroPython. Actual requirements vary per module
(basicly, if module is not related to I/O, it should work without
problem on baremetal ports too).

Usage
-----
micropython-lib packages are published on PyPI (Python Package Index),
standard Python community package repository: http://pypi.python.org/ .
You can search for MicroPython related packages, read additional info,
etc.

To install packages from PyPI for usage on your local system, use
"pip-micropython" tool, which is a simple wrapper around a standard
"pip" tool, which is used to install package for CPython.
"pip-micropython" tool can be found in "tools" subdirectory of the main
MicroPython repository (https://github.com/micropython/micropython).
Just install "pip-micropython" script somewhere on your PATH.

Afterwards, just use pip-micropython in a way similar to pip:

~~~~
$ pip-micropython install micropython-copy
$ micropython
>>> import copy
>>> copy.copy([1, 2, 3])
[1, 2, 3]
~~~~

Review pip-micropython source code for more info.

Development
-----------
To install modules during development, use "make install". By default, it
will install all available packages. You can pass MOD=<module> parameter
to install specific module.

Links
-----
More info:

 * https://github.com/micropython/micropython/issues/405
 * http://forum.micropython.org/viewtopic.php?f=5&t=70

Basic guidelines for installing packages from PyPI:

 * https://github.com/micropython/micropython/issues/413
