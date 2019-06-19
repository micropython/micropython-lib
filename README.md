# micropython-lib

micropython-lib is a project to develop a non-monolithic standard library
for MicroPython. Each module comes from one of the following sources (and thus
each module has its own licensing terms):

* written from scratch specifically for MicroPython.
* ported from CPython.
* ported from some other Python implementation, e.g. PyPy.
* some modules actually aren't yet implemented and are dummy.

The version of the library in this repository is compatible with
[official MicroPython](https://github.com/micropython/micropython.git) 
including firmware builds downloaded from [micropython.org](https://micropython.org/).

Paul Sokolovsky's [Pycopy](https://github.com/pfalcon/micropython) MicroPython
fork requires [this library version](https://github.com/pfalcon/micropython-lib).
Some modules in this library are incompatible with official MicroPython. Pycopy
users should follow installation instructions on the above library site.

The following notes apply to users of official MicroPython.

To aid installation, library modules are available on [PyPi](https://pypi.org/)
however the normal `pip` and `pip3` tools cannot be used. MicroPython provides
a `upip.py` version optimised to run on microcontrollers. The library modules
on PyPi are those compatible with the Pycopy fork. Where those are incompatible
with official MicroPython, the official version of `upip` will ensure that the
correct module version is acquired from an alternative repository.

Usage of `upip` is documented 
[here](http://docs.micropython.org/en/latest/reference/packages.html).

# 1. General notes on library modules

Many CPython library modules are unsuited for use on microcontrollers, either
by virtue of their application domain or in consequence of their size and
complexity. Modules in this MicroPython library are optimised to run
efficiently in resource constrained environments. Functionality is typically a
subset of the CPython version; rarely there are extensions, typically by reason
of performance.

Some library modules have names prefixed with "u": this signifies a "micro"
version of a CPython library; the name avoids conflict should the full version
also be installed. Thus `uasyncio` is a "micro" version of `asyncio` optimised
for high performance on microcontrollers.

The firmware build for each hardware device will have a set of library modules
pre-installed. For example network enabled devices have `upip` installed.
Before installing a library module check if it is already present.

Hardware devices running MicroPython will search for library modules in their
filesystem and also in a `lib` subdirectory if one is provided:
```python
>>> import sys
>>> sys.path
['', '/flash', '/flash/lib']
>>> 
```

# 2. Searching for modules

On [PyPi](https://pypi.org/), you can search for MicroPython related packages
and read additional package information. By convention, all micropython-lib
package names are prefixed with "micropython-". The reverse is not true - some
package starting with "micropython-" aren't part of micropython-lib and were
released by third parties.

Appropriately tagged packages may be browsed
[via this URL](https://pypi.org/search/?q=&o=&c=Programming+Language+%3A%3A+Python+%3A%3A+Implementation+%3A%3A+MicroPython).

# 3. Installing on networked hardware

To install a library module on a device with network connectivity (such as a
Pyboard D) ensure that the firmware build is version 1.11 or later. This will
ensure that the right version of `upip` is available at the REPL.

The following illustrates installing the `umqtt.simple` module to a Pyboard D.
It assumes you have a `do_connect.py` script which authenticates the device on
your LAN, and that internet connectivity exists. At the REPL:
```
>>> import do_connect
connecting to network...
network config: ('192.168.0.33', '255.255.255.0', '192.168.0.1', '208.67.220.220')
MAC 48:4a:30:01:b3
>>> import upip
>>> upip.install('micropython-umqtt.simple')
Installing to: /flash/
Warning: micropython.org SSL certificate is not validated
Installing micropython-umqtt.simple 1.3.4 from https://micropython.org/pi/umqtt.simple/umqtt.simple-1.3.4.tar.gz
>>>  
```

# 4. Installing on non-networked hardware

There are three approaches. All involve copying the files to your PC then
copying them to your hardware. A number of tools are available for the latter
operation, but [rshell](https://github.com/dhylands/rshell) is highly
recommended.

## 4.1 Method 1: clone and copy

This entire repository may be copied to your PC with
```
$ git clone https://github.com/micropython/micropython-lib
```
You will then need to locate and copy the files relevant to the module you wish
to install. Assume you want to install the `pickle` module to a Pyboard 1.x.
Running `rshell` from your local `micropython-lib` directory, issue:
```
/some_path/micropython-lib> mkdir /flash/lib
/some_path/micropython-lib> cp pickle/* /flash/lib
```
Note that for some modules there may be dependencies which must be installed.
Also some modules are implemented as Python packages requiring a directory tree
to be copied.

## 4.2 Method 2: upip

This requires that the Unix build of MicroPython be installed on the PC. This
has to be built from source. Assuming that the executable `micropython` is on
your search path, the following will create a directory `foo` and populate it
with the file for `pickle`.

```
[adminpete@capybara]: ~
$ micropython -m upip install -p foo micropython-pickle
Installing to: foo/
Warning: micropython.org SSL certificate is not validated
Installing micropython-pickle 0.1 from https://micropython.org/pi/pickle/pickle-0.1.tar.gz
[adminpete@capybara]: ~
$ ls foo
pickle.py
```

## 4.3 Method 3: micropip

This is intended for those not wishing to compile the Unix build. This
unofficial program is a version of `upip` adapted to run on a PC under CPython
version 3.2 or above; it provides similar functionality. The following assumes
that `micropip.py` is on your path and has executable privilege.
```
[adminpete@capybara]: ~
$ micropip.py install -p ~/foo micropython-pickle
Installing to: /home/adminpete/foo/
Warning: micropython.org SSL certificate is not validated
Installing micropython-pickle 0.1 from https://micropython.org/resources/upi/micropython-pickle/micropython-pickle-0.1.tar.gz
[adminpete@capybara]: ~
```
Micropip is available [here](https://github.com/peterhinch/micropython-samples/blob/master/micropip/micropip.py).

## 4.4 Copying to target hardware

This example illustrates the use of [rshell](https://github.com/dhylands/rshell)
to copy the results of the above examples of using `upip` or `micropip` to a
Pyboard 1.1.
```
[adminpete@capybara]: ~
$ cd foo
[adminpete@capybara]: ~/foo
$ rshell cp -r * /sd
Using buffer-size of 32
Connecting to /dev/pyboard (buffer-size 32)...
Trying to connect to REPL  connected
Testing if ubinascii.unhexlify exists ... Y
Retrieving root directories ... /flash/ /sd/
Setting time ... Jun 18, 2019 18:06:07
Evaluating board_name ... pyboard
Retrieving time epoch ... Jan 01, 2000
[adminpete@capybara]: ~/foo
```

# 5. Installing on the Unix build

To install packages from PyPI for usage on your local system, use the `upip`
tool. This is bundled with MicroPython "Unix" port (i.e. if you build "Unix"
port, you automatically have `upip` tool). The following example assumes that
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

## 5.1 Development

To install modules during development, use `make install`. By default, all
available packages will be installed. To install a specific module, add the
`MOD=<module>` parameter to the end of the `make install` command.

# 6. Links

If you would like to trace evolution of MicroPython packaging support,
you may find following links useful (note that they may contain outdated
information):

 * https://github.com/micropython/micropython/issues/405
 * http://forum.micropython.org/viewtopic.php?f=5&t=70

Guidelines for packaging MicroPython modules for PyPI:

 * https://github.com/micropython/micropython/issues/413
