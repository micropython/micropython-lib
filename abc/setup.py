import sys
# Remove current dir from sys.path, otherwise setuptools will peek up our
# module instead of system.
sys.path.pop(0)
from setuptools import setup


setup(name='micropython-abc',
      version='0.0.0',
      description='Dummy abc module for MicroPython',
      long_description='This is a dummy implementation of a module for MicroPython standard library.\nIt contains zero or very little functionality, and primarily intended to\navoid import errors (using idea that even if an application imports a\nmodule, it may be not using it onevery code path, so may work at least\npartially). It is expected that more complete implementation of the module\nwill be provided later. Please help with the development if you are\ninterested in this module.',
      url='https://github.com/micropython/micropython/issues/405',
      author='MicroPython Developers',
      author_email='micro-python@googlegroups.com',
      maintainer='MicroPython Developers',
      maintainer_email='micro-python@googlegroups.com',
      license='MIT',
      py_modules=['abc'])
