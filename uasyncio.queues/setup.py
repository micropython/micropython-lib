import sys
# Remove current dir from sys.path, otherwise setuptools will peek up our
# module instead of system.
sys.path.pop(0)
from setuptools import setup


setup(name='micropython-uasyncio.queues',
      version='0.1',
      description='uasyncio.queues module for MicroPython',
      long_description='Port of asyncio.queues to uasyncio.',
      url='https://github.com/micropython/micropython/issues/405',
      author='MicroPython Developers',
      author_email='micro-python@googlegroups.com',
      maintainer='MicroPython Developers',
      maintainer_email='micro-python@googlegroups.com',
      license='MIT',
      packages=['uasyncio'],
      install_requires=['micropython-uasyncio.core', 'micropython-collections.deque'])
