import sys
# Remove current dir from sys.path, otherwise distutils will peek up our
# module instead of system.
sys.path.pop(0)
from setuptools import setup

setup(name='micropython-random',
      version='0.0.0',
      description='dummy random module to MicroPython',
      url='https://github.com/micropython/micropython/issues/405',
      author='MicroPython Developers',
      author_email='micro-python@googlegroups.com',
      license='MIT',
      py_modules=['random'])
