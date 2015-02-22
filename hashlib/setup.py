import sys
# Remove current dir from sys.path, otherwise setuptools will peek up our
# module instead of system.
sys.path.pop(0)
from setuptools import setup


setup(name='micropython-hashlib',
<<<<<<< HEAD
      version='2.4.0-1',
      description='PyPy hashlib module ported to MicroPython',
      long_description='This is a module ported from PyPy standard library to be compatible with\nMicroPython interpreter. Usually, this means applying small patches for\nfeatures not supported (yet, or at all) in MicroPython. Sometimes, heavier\nchanges are required. Note that CPython modules are written with availability\nof vast resources in mind, and may not work for MicroPython ports with\nlimited heap. If you are affected by such a case, please help reimplement\nthe module from scratch.',
=======
      version='0.0.1',
      description='Implementation of basic hashlib functions for MicroPython',
      long_description='This is a dummy implementation of a module for MicroPython standard library.\nIt contains zero or very little functionality, and primarily intended to\navoid import errors (using idea that even if an application imports a\nmodule, it may be not using it onevery code path, so may work at least\npartially). It is expected that more complete implementation of the module\nwill be provided later. Please help with the development if you are\ninterested in this module.',
>>>>>>> hashlib: Pure python implementation of sha224, sha256, sha384, sha512
      url='https://github.com/micropython/micropython/issues/405',
      author='PyPy Developers',
      author_email='pypy-dev@python.org',
      maintainer='MicroPython Developers',
      maintainer_email='micro-python@googlegroups.com',
      license='MIT',
      packages=['hashlib'])
