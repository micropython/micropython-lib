#rng = 'lcg'
rng = 'xorshift'
if rng == 'xorshift':
    try:
        import sys
        if sys.platform == 'pyboard':
            from xorshift_pyb import Random
        else:
            from sys import maxsize
            if maxsize > 1<<60:
                from xorshift_py_64 import Random
            else:
                from warnings import warn as _warn
                _warn("Can't use xorshift, falling back to lcg")
                from lcg import Random
    except Exception as e:
        from warnings import warn as _warn
        _warn(e)
        _warn("Can't use xorshift, falling back to lcg")
        from lcg import Random
else:
    from lcg import Random
