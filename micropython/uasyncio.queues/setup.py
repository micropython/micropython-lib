import sys
# Remove current dir from sys.path, otherwise setuptools will peek up our
# module instead of system's.
sys.path.pop(0)
from setuptools import setup
sys.path.append("..")
import sdist_upip

setup(name='micropython-uasyncio.queues',
      version='0.1.2',
      description='uasyncio.queues module for MicroPython',
      long_description='Port of asyncio.queues to uasyncio.',
      url='https://github.com/micropython/micropython-lib',
      author='micropython-lib Developers',
      author_email='micro-python@googlegroups.com',
      maintainer='micropython-lib Developers',
      maintainer_email='micro-python@googlegroups.com',
      license='MIT',
      cmdclass={'sdist': sdist_upip.sdist},
      packages=['uasyncio'],
      install_requires=['micropython-uasyncio.core', 'micropython-collections.deque'])
