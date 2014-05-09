import sys
# Remove current dir from sys.path, otherwise distutils will peek up our
# module instead of system one.
sys.path.pop(0)
sys.path.insert(0, '..')
from setuptools import setup
import metadata

NAME = 'datetime'

setup(name='micropython-' + NAME,
      version='0.0.0',
      description=metadata.desc_dummy(NAME),
      url=metadata.url,
      author=metadata.author_upy_devels,
      author_email=metadata.author_upy_devels_email,
      license='MIT',
      py_modules=[NAME])
