micropython-lib
===============

This is a repository of libraries designed to be useful for writing
MicroPython applications.

The libraries here fall into four categories corresponding to the four top-level directories:

 * **python-stdlib**: Compatible versions of modules from the [Python Standard Library](https://docs.python.org/3/library/). These should be drop-in replacements for the Python libraries, although many have reduced functionality or missing methods or classes (which may not be an issue for many most cases).

 * **python-ecosys**: Compatible, but reduced-functionality versions of modules from the larger Python ecosystem, for example that might be found in the [Python Package Index](https://pypi.org/).

* **micropython**: MicroPython-specific modules that do not have equivalents in other Python environments. These are typically hardware drivers or highly-optimised alternative implementations of functionality available in other Python modules.

 * **unix-ffi**: These modules are specifically for the MicroPython Unix port and provide access to operating-system and third-party libraries via FFI.

Usage
-----

Many libraries are self contained modules, and you can quickly get started by
copying the relevant Python file to your device. For example, to add the
`base64` library, you can directly copy `python-stdlib/base64/base64.py` to the `lib`
directory on your device.

Other libraries are packages, in which case you'll need to copy the directory instead. For example, to add `collections.defaultdict`, copy `collections/collections/__init__.py` and `collections.defaultdict/collections/defaultdict.py` to a directory named `lib/collections` on your device.

Developer Guidance
------------------

To everyone interested in contributing here, thank you! While we might take a while to get back to you (resources / man-hours are tight) we do value your efforts.

To make reviews quicker & easier, please try to follow these guidelines as much as possible:

* Submit packages to the corect folder; in particular packages in `python-stdlib` should only have functions that match the api (or a subset thereof) of the cpython standard library equivalent. If you want to add extra functionality, please put that in a separate / companion package that can be submitted to a different folder.

* If you're adding changes / new packages that match existing cpython ones, please include a link to the matching cpython docs in the MR.

* For a new package, try to fill out the `setup.py` and `metadata.txt` as best you can, looking at other ones here as example.
  - In particular with `python-stdlib` packages, note whether it's a copy of the cpython module patched for compatibility vs a re-implementation to match the api.

* When pushing commits / opening MR's please try to match the format `package/name: Description of change.`  
  Take a look at the git history [here](https://github.com/micropython/micropython-lib/commits/master) for examples.

* Unit tests are highly encouraged! Passing tests make for quicker reviews!

* Please run `pip3 install -U black; python3 tools/codeformat.py ./path/to/my/module` before committing changes to ensure the formatting matches the standard here.

* If you want / need to use your package faster than we can get back to you here, remember you're also more than welcome to keep your packages in personal repo's and [publish on PyPI](https://docs.micropython.org/en/latest/reference/packages.html) for use with upip! If you run into issues with this process you can still raise an issue here and we'll try to assist.

Future plans (and new contributor ideas)
----------------------------------------

* Provide compiled .mpy distributions.
* Develop a set of example programs using these libraries.
* Develop more MicroPython libraries for common tasks.
* Provide a replacement for the previous `upip` tool.
