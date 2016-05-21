import sys
# Remove current dir from sys.path, otherwise setuptools will peek up our
# module instead of system.
sys.path.pop(0)
from setuptools import setup


setup(name='micropython-os',
      version='0.4.2',
      description='os module for MicroPython',
      long_description="This is a module reimplemented specifically for MicroPython standard library,\nwith efficient and lean design in mind. Note that this module is likely work\nin progress and likely supports just a subset of CPython's corresponding\nmodule. Please help with the development if you are interested in this\nmodule.",
      url='https://github.com/micropython/micropython/issues/405',
      author='Paul Sokolovsky',
      author_email='micro-python@googlegroups.com',
      maintainer='MicroPython Developers',
      maintainer_email='micro-python@googlegroups.com',
      license='MIT',
      packages=['os'],
      install_requires=['micropython-ffilib', 'micropython-errno', 'micropython-stat'])
