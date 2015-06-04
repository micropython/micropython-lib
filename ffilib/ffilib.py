import ffi

_cache = {}

def open(name, maxver=10, extra=()):
    try:
        return _cache[name]
    except KeyError:
        pass
    err = None
    for n in ("%s.so" % name, "%s.dylib" % name):
        try:
            l = ffi.open(n)
            _cache[name] = l
            return l
        except OSError as e:
            err = e
    for i in range(maxver):
        try:
            l = ffi.open("%s.so.%u" % (name, i))
            _cache[name] = l
            return l
        except OSError as e:
            err = e
    for n in extra:
        try:
            l = ffi.open(n)
            _cache[name] = l
            return l
        except OSError as e:
            err = e
    raise err
