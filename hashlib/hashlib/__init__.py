try:
    import uhashlib
    sha256 = uhashlib.sha256

    if hasattr(uhashlib, 'sha1'):
        sha1 = uhashlib.sha1

    if hasattr(uhashlib, 'sha512'):
        sha512 = uhashlib.sha512
    else:
        from .sha512 import sha512

except ImportError:
    from .sha256 import sha256
    from .sha512 import sha512
    uhashlib = {}

def new(algo, data=b''):

    if algo in dir(uhashlib):
        pp = getattr(uhashlib, algo)
        return pp(data)

    if algo == 'sha256':
        from .sha256 import sha256
        return sha256(data)

    if algo == 'sha224':
        from .sha256 import sha224
        return sha224(data)

    if algo == 'sha384':
        from .sha512 import sha384
        return sha384(data)

    if algo == 'sha512':
        from .sha512 import sha512
        return sha512(data)

    raise ValueError(algo)

