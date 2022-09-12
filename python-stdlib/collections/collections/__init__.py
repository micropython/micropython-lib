# Replace built-in collections module.
from ucollections import *

# Provide optional dependencies (which may be installed separately).
try:
    from .defaultdict import defaultdict
except ImportError:
    pass
try:
    from .deque import deque
except ImportError:
    pass


class MutableMapping:
    pass
