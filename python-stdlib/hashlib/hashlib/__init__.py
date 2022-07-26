try:
    import uhashlib
except ImportError:
    uhashlib = None


def init():
    for i in ("sha1", "sha224", "sha256", "sha384", "sha512"):
        try:
            c = __import__("_" + i, None, None, (), 1)
        except ImportError:
            c = uhashlib
        c = getattr(c, i, None)
        globals()[i] = c


init()


def new(algo, data=b""):
    try:
        c = globals()[algo]
        return c(data)
    except KeyError:
        raise ValueError(algo)
