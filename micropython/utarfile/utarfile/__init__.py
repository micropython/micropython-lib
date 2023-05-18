from .utarfile import *

try:
  from .write import TarInfoWrite, TarFileWrite

  for method in TarInfoWrite.added_methods:
    setattr(TarInfo, method, getattr(TarInfoWrite, method))
  for method in TarFileWrite.added_methods:
    setattr(TarFile, method, getattr(TarFileWrite, method))

except ImportError:
  pass
