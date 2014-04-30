import sys
# Remove current dir from sys.path, otherwise distutils will peek up our
# module instead of system.
sys.path.pop(0)
from setuptools import setup

setup(name='micropython-multiprocessing',
      version='0.0.1',
      description='multiprocessing module to MicroPython',
      url='https://github.com/micropython/micropython/issues/405',
      author='Paul Sokolovsky',
      author_email='micro-python@googlegroups.com',
      license='MIT',
      install_requires=['micropython-os'],
      py_modules=['multiprocessing'])
