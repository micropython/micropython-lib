import ffi


_h = None

names = ('libc.so', 'libc.so.0', 'libc.so.6')

def get():
    global _h
    if _h:
        return _h
    err = None
    for n in names:
        try:
            _h = ffi.open(n)
            return _h
        except OSError as e:
            err = e
    raise err


def set_names(n):
    global names
    names = n
