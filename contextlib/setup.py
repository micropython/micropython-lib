import sys
# Remove current dir from sys.path, otherwise setuptools will peek up our
# module instead of system.
sys.path.pop(0)
from setuptools import setup


setup(name='micropython-contextlib',
      version='3.4.2-0',
      description='Port of contextlib for micropython',
      long_description='Port of contextlib for micropython',
      author='MicroPython Developers',
      author_email='micro-python@googlegroups.com',
      maintainer='MicroPython Developers',
      maintainer_email='micro-python@googlegroups.com',
      license='MIT',
      packages=['contextlib'],
      install_requires=['micropython-unittest'])
