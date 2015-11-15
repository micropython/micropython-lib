import sys
# Remove current dir from sys.path, otherwise setuptools will peek up our
# module instead of system.
sys.path.pop(0)
from setuptools import setup


setup(name='micropython-urllib.parse',
      version='0.5.1',
      description='CPython urllib.parse module ported to MicroPython',
      long_description='This is a module ported from CPython standard library to be compatible with\nMicroPython interpreter. Usually, this means applying small patches for\nfeatures not supported (yet, or at all) in MicroPython. Sometimes, heavier\nchanges are required. Note that CPython modules are written with availability\nof vast resources in mind, and may not work for MicroPython ports with\nlimited heap. If you are affected by such a case, please help reimplement\nthe module from scratch.',
      url='https://github.com/micropython/micropython/issues/405',
      author='CPython Developers',
      author_email='python-dev@python.org',
      maintainer='MicroPython Developers',
      maintainer_email='micro-python@googlegroups.com',
      license='Python',
      packages=['urllib'],
      install_requires=['micropython-re-pcre', 'micropython-collections', 'micropython-collections.defaultdict'])
