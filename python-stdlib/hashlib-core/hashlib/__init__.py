# Use built-in algorithms preferentially (on many ports this is just sha256).
try:
    from uhashlib import *
except ImportError:
    pass


# Add missing algorithms based on installed extensions.
def _init():
    for algo in ("sha224", "sha256", "sha384", "sha512"):
        if algo not in globals():
            try:
                # from ._{algo} import {algo}
                c = __import__("_" + algo, None, None, (), 1)
                globals()[algo] = getattr(c, algo)
            except ImportError:
                pass


_init()
del _init


def new(algo, data=b""):
    try:
        c = globals()[algo]
        return c(data)
    except KeyError:
        raise ValueError(algo)
