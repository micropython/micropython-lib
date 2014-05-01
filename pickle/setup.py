import sys
# Remove current dir from sys.path, otherwise distutils will peek up our
# module instead of system.
sys.path.pop(0)
from setuptools import setup

setup(name='micropython-pickle',
      version='0.0.1',
      description='pickle module to MicroPython',
      url='https://github.com/micropython/micropython/issues/405',
      author='Paul Sokolovsky',
      author_email='micro-python@googlegroups.com',
      license='MIT',
      py_modules=['pickle'])
