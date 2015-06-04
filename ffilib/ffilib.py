import sys
import ffi

_cache = {}

def open(name, maxver=10, extra=()):
    try:
        return _cache[name]
    except KeyError:
        pass
    def libs():
        if sys.platform == "linux":
            yield '%s.so' % name
            for i in range(maxver, -1, -1):
                yield '%s.so.%u' % (name, i)
        else:
            for ext in ('dylib', 'dll'):
                yield '%s.%s' % (name, ext)
        for n in extra:
            yield n
    err = None
    for n in libs():
        try:
            l = ffi.open(n)
            _cache[name] = l
            return l
        except OSError as e:
            err = e
    raise err
