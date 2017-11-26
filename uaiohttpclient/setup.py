import sys
# Remove current dir from sys.path, otherwise setuptools will peek up our
# module instead of system's.
sys.path.pop(0)
from setuptools import setup
sys.path.append("..")
import optimize_upip

setup(name='micropython-uaiohttpclient',
      version='0.5',
      description='HTTP client module for MicroPython uasyncio module',
      long_description=open('README').read(),
      url='https://github.com/micropython/micropython-lib',
      author='Paul Sokolovsky',
      author_email='micro-python@googlegroups.com',
      maintainer='MicroPython Developers',
      maintainer_email='micro-python@googlegroups.com',
      license='MIT',
      cmdclass={'optimize_upip': optimize_upip.OptimizeUpip},
      py_modules=['uaiohttpclient'])
