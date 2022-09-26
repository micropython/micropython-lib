__all__ = [ "register", "unregister", ]
_exitfuncs = []

import sys
if hasattr(sys, "atexit"):
    def _exitfunc():
        for f, a, k in _exitfuncs:
            f(*a, **k)
    sys.atexit(_exitfunc)

def register(func, *args, **kwargs):
    _exitfuncs.append((func, args, kwargs))
    return func

def unregister(func):
    global _exitfuncs
    _exitfuncs = [ (f, a, k)
                   for f, a, k in _exitfuncs
                   if f is not func ]
