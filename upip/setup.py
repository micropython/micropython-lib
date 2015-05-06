import sys
# Remove current dir from sys.path, otherwise setuptools will peek up our
# module instead of system.
sys.path.pop(0)
from setuptools import setup


setup(name='micropython-upip',
      version='0.5.1',
      description='Simple package manager for MicroPython.',
      long_description='Simple package manager for MicroPython, targetting to be self-hosted (but not yet there). Compatible only with packages without custom setup.py code.',
      url='https://github.com/micropython/micropython/issues/405',
      author='Paul Sokolovsky',
      author_email='micro-python@googlegroups.com',
      maintainer='MicroPython Developers',
      maintainer_email='micro-python@googlegroups.com',
      license='MIT',
      py_modules=['upip', 'upip__libc', 'upip_errno', 'upip_gzip', 'upip_os', 'upip_os_path', 'upip_stat', 'upip_utarfile'])
