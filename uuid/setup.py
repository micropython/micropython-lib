import sys
# Remove current dir from sys.path, otherwise setuptools will peek up our
# module instead of system's.
sys.path.pop(0)
from setuptools import setup
sys.path.append("..")
import sdist_upip

setup(name='micropython-uuid',
      version='0.0.2',
      description='Basic uuid module for MicroPython',
      long_description='This implementation only provides a uuid4() function returning a random uuid string',
      url='https://github.com/micropython/micropython-lib',
      author='micropython-lib Developers',
      author_email='micro-python@googlegroups.com',
      maintainer='micropython-lib Developers',
      maintainer_email='micro-python@googlegroups.com',
      license='MIT',
      cmdclass={'sdist': sdist_upip.sdist},
      py_modules=['uuid'])
