# MicroPython gzip module
# MIT license; Copyright (c) 2023 Jim Mussared

_WBITS = const(15)

import builtins, io, deflate


def GzipFile(fileobj):
    return deflate.DeflateIO(fileobj, deflate.GZIP, _WBITS)


def open(filename, mode="rb"):
    return deflate.DeflateIO(builtins.open(filename, mode), deflate.GZIP, _WBITS, True)


if hasattr(deflate.DeflateIO, "write"):

    def compress(data):
        f = io.BytesIO()
        with GzipFile(fileobj=f) as g:
            g.write(data)
        return f.getvalue()


def decompress(data):
    f = io.BytesIO(data)
    with GzipFile(fileobj=f) as g:
        return g.read()
