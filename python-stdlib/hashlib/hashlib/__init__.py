try:
    import uhashlib
except ImportError:
    uhashlib = None


def init():
    for i in ("sha1", "sha224", "sha256", "sha384", "sha512"):
        # first try to import the python-stdlib hash so that we are compatible
        # with e.g. hmac (uhashlib lacks {digest,block}_size, copy())
        try:
            c = __import__("_" + i, None, None, (), 1)
            c = getattr(c, i)
        except ImportError:
            c = None
        # fallback to uhashlib (e.g. sha1)
        if not c:
            c = getattr(uhashlib, i, None)
        if c:
            globals()[i] = c


init()


def new(algo, data=b""):
    try:
        c = globals()[algo]
        return c(data)
    except KeyError:
        raise ValueError(algo)
