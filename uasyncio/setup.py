import sys
# Remove current dir from sys.path, otherwise setuptools will peek up our
# module instead of system's.
sys.path.pop(0)
from setuptools import setup
sys.path.append("..")
import optimize_upip

setup(name='micropython-uasyncio',
      version='1.4',
      description='Lightweight asyncio-like library for MicroPython, built around native Python coroutines.',
      long_description=open('README.rst').read(),
      url='https://github.com/micropython/micropython-lib',
      author='Paul Sokolovsky',
      author_email='micro-python@googlegroups.com',
      maintainer='MicroPython Developers',
      maintainer_email='micro-python@googlegroups.com',
      license='MIT',
      cmdclass={'optimize_upip': optimize_upip.OptimizeUpip},
      packages=['uasyncio'],
      install_requires=['micropython-uasyncio.core'])
