import sys
# Remove current dir from sys.path, otherwise setuptools will peek up our
# module instead of system.
sys.path.pop(0)
from setuptools import setup


setup(name='micropython-ucontextlib',
      version='0.1',
      description='ucontextlib module for MicroPython',
      long_description='Minimal subset of contextlib for MicroPython low-memory ports',
      url='https://github.com/micropython/micropython/issues/405',
      author='MicroPython Developers',
      author_email='micro-python@googlegroups.com',
      maintainer='MicroPython Developers',
      maintainer_email='micro-python@googlegroups.com',
      license='Python',
      py_modules=['ucontextlib'])
