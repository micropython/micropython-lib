import sys
# Remove current dir from sys.path, otherwise distutils will peek up our
# module instead of system.
sys.path.pop(0)
from setuptools import setup


def desc_dummy(name):
    return 'Dummy %s module to MicroPython' % name
def desc_cpython(name):
    return 'CPython %s module ported to MicroPython' % name
def desc_upython(name):
    return '%s module for MicroPython' % name

NAME = 'socket'

setup(name='micropython-' + NAME,
      version='0.0.1',
      description=desc_upython(NAME),
      url='https://github.com/micropython/micropython/issues/405',
      author='MicroPython Developers',
      author_email='micro-python@googlegroups.com',
      license='MIT',
      py_modules=[NAME])
