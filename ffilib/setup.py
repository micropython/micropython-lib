import sys
# Remove current dir from sys.path, otherwise setuptools will peek up our
# module instead of system.
sys.path.pop(0)
from setuptools import setup


setup(name='micropython-ffilib',
      version='0.1.1',
      description='MicroPython FFI helper module',
      long_description='MicroPython FFI helper module to easily interface with underlying shared libraries',
      url='https://github.com/micropython/micropython/issues/405',
      author='Damien George',
      author_email='micro-python@googlegroups.com',
      maintainer='MicroPython Developers',
      maintainer_email='micro-python@googlegroups.com',
      license='MIT',
      py_modules=['ffilib'])
