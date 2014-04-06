import sys
# Remove current dir from sys.path, otherwise distutils will peek up our
# copy module instead of system.
sys.path.pop(0)
from distutils.core import setup

setup(name='micropython-copy',
      version='0.0.1',
      description='CPython copy module ported to MicroPython',
      url='https://github.com/micropython/micropython/issues/405',
      author='CPython Developers',
      maintainer='MicroPython Developers',
      maintainer_email='micro-python@googlegroups.com',
      license='Python',
      py_modules=['copy'])
