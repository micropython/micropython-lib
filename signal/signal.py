import _libc


SIG_DFL = 0
SIG_IGN = 1

SIGINT = 2
SIGPIPE = 13
SIGTERM = 15

libc = _libc.get()

signal_ = libc.func("i", "signal", "ii")

def signal(n, handler):
    if isinstance(handler, int):
        return signal_(n, handler)
    raise NotImplementedError
