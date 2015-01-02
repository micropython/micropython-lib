import sys
# Remove current dir from sys.path, otherwise setuptools will peek up our
# module instead of system.
sys.path.pop(0)
from setuptools import setup


setup(name='micropython-cpython-uasyncio',
      version='0.1',
      description='MicroPython module uasyncio ported to CPython',
      long_description='This is MicroPython compatibility module, allowing applications using\nMicroPython-specific features to run on CPython.\n',
      url='https://github.com/micropython/micropython/issues/405',
      author='MicroPython Developers',
      author_email='micro-python@googlegroups.com',
      maintainer='MicroPython Developers',
      maintainer_email='micro-python@googlegroups.com',
      license='Python',
      py_modules=['uasyncio'])
