import sys
# Remove current dir from sys.path, otherwise setuptools will peek up our
# module instead of system's.
sys.path.pop(0)
from setuptools import setup
sys.path.append("..")
import sdist_upip

setup(name='micropython-uasyncio.core',
      version='2.0',
      description='Lightweight asyncio-like library for MicroPython, built around native Python coroutines. (Core event loop).',
      long_description='Lightweight asyncio-like library for MicroPython, built around native Python coroutines. (Core event loop).',
      url='https://github.com/micropython/micropython-lib',
      author='Paul Sokolovsky',
      author_email='micro-python@googlegroups.com',
      maintainer='micropython-lib Developers',
      maintainer_email='micro-python@googlegroups.com',
      license='MIT',
      cmdclass={'sdist': sdist_upip.sdist},
      packages=['uasyncio'])
