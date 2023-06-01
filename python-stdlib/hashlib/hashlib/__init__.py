# Use built-in functions preferentially (on most ports this is just sha256).
try:
    from uhashlib import *
except ImportError:
    pass


# Add missing functions.
if "sha224" not in globals():
    from ._sha256 import sha224
if "sha256" not in globals():
    from ._sha256 import sha256
if "sha384" not in globals():
    from ._sha512 import sha384
if "sha512" not in globals():
    from ._sha512 import sha512


def new(algo, data=b""):
    try:
        c = globals()[algo]
        return c(data)
    except KeyError:
        raise ValueError(algo)
