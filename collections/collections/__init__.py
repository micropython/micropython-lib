# Should be reimplemented for MicroPython
# Reason:
# CPython implementation brings in metaclasses and other bloat.
# This is going to be just import-all for other modules in a namespace package
from _collections import *
