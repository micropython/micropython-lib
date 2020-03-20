micropython-lib
===============

This is a repository of libraries designed to be useful for writing
MicroPython applications.

The libraries here fall into roughly four categories:

 * Compatible ports of CPython standard libraries. These should be drop-in replacements for the CPython libraries, although many have reduced functionality or missing methods or classes (which may not be an issue for many use cases).

 * "Micro" versions of CPython standard libraries with limited compatibility. These can often provide the same functionality, but might require some code changes compared to the CPython version.

 * MicroPython-specific libraries. These include drivers and other libraries targeted at running Python on hardware or embedded systems.

 * MicroPython-on-Unix-specific libraries. These extend the functionality of the Unix port to allow access to operating-system level functionality (which allows more CPython compatibility).

Usage
-----

Many libraries are self contained modules, and you can quickly get started by
copying the relevant Python file to your device. For example, to add the
`base64` library, you can directly copy `base64/base64.py` to the `lib`
directory on your device.

Other libraries are packages, in which case you'll need to copy the directory instead. For example, to add `collections.defaultdict`, copy `collections/collections/__init__.py` and `collections.defaultdict/collections/defaultdict.py` to a directory named `lib/collections` on your device.

For devices that have network connectivity (e.g. PYBD, ESP8266, ESP32), they
will have the `upip` module installed.

```
>>> import upip
>>> upip.install('micropython-base64')
>>> upip.install('micropython-collections.defaultdict')
...
>>> import base64
>>> base64.b64decode('aGVsbG8sIG1pY3JvcHl0aG9u')
b'hello, micropython'
>>> from collections import defaultdict
>>> d = defaultdict(int)
>>> d[a] += 1
```

Future plans (and new contributor ideas)
----------------------------------------

* Provide compiled .mpy distributions.
* Develop a set of example programs using these libraries.
* Develop more MicroPython libraries for common tasks.
