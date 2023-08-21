# Include built-in os module.
import sys
__path = sys.path
try:
    sys.path.clear()
    from os import *
finally:
    sys.path.extend(__path)

# Provide optional dependencies (which may be installed separately).
try:
    from . import path
except ImportError:
    pass
