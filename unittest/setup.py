import sys
# Remove current dir from sys.path, otherwise setuptools will peek up our
# module instead of system's.
sys.path.pop(0)
from setuptools import setup
sys.path.append("..")
import sdist_upip

setup(name='micropython-unittest',
      version='0.3.2',
      description='unittest module for MicroPython',
      long_description="This is a module reimplemented specifically for MicroPython standard library,\nwith efficient and lean design in mind. Note that this module is likely work\nin progress and likely supports just a subset of CPython's corresponding\nmodule. Please help with the development if you are interested in this\nmodule.",
      url='https://github.com/micropython/micropython-lib',
      author='micropython-lib Developers',
      author_email='micro-python@googlegroups.com',
      maintainer='micropython-lib Developers',
      maintainer_email='micro-python@googlegroups.com',
      license='MIT',
      cmdclass={'sdist': sdist_upip.sdist},
      py_modules=['unittest'])
