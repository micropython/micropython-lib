# Replace built-in collections module.
from ucollections import *

# Provide optional dependencies (which may be installed separately).
try:
    from .defaultdict import defaultdict
except ImportError:
    pass
# optional collections.abc typing dummy module
try:
    # cannot use relative import here
    import collections.abc as abc
    import sys
    sys.modules['collections.abc'] = abc
except ImportError:
    pass


class MutableMapping:
    pass
