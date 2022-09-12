# Replace built-in os module.
from uos import *

# Provide optional dependencies (which may be installed separately).
try:
    from . import path
except ImportError:
    pass
