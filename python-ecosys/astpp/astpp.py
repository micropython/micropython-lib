try:
    from micropython import const
except ImportError:

    def const(x):
        return x


def keep(obj):
    return obj


def omit(obj):
    return None


def keep_if(cond):
    return keep if cond else omit


def omit_if(cond):
    return omit if cond else keep


try:
    import micropython as _real_mpy
except ImportError:
    _real_mpy = None
if _real_mpy is not None:
    micropython = _real_mpy
else:

    class _MicroPythonShim:
        native = staticmethod(keep)
        viper = staticmethod(keep)

    micropython = _MicroPythonShim()
__version__ = "0.1.3"
