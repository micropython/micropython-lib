# MicroPython zlib module
# MIT license; Copyright (c) 2023 Jim Mussared

import io, deflate

_MAX_WBITS = const(15)


def _decode_wbits(wbits, decompress):
    if -15 <= wbits <= -5:
        return (
            deflate.RAW,
            -wbits,
        )
    elif 5 <= wbits <= 15:
        return (deflate.ZLIB, wbits)
    elif decompress and wbits == 0:
        return (deflate.ZLIB,)
    elif 21 <= wbits <= 31:
        return (deflate.GZIP, wbits - 16)
    elif decompress and 35 <= wbits <= 47:
        return (deflate.AUTO, wbits - 32)
    else:
        raise ValueError("wbits")


if hasattr(deflate.DeflateIO, "write"):

    def compress(data, wbits=_MAX_WBITS):
        f = io.BytesIO()
        with deflate.DeflateIO(f, *_decode_wbits(wbits, False)) as g:
            g.write(data)
        return f.getvalue()


def decompress(data, wbits=_MAX_WBITS):
    f = io.BytesIO(data)
    with deflate.DeflateIO(f, *_decode_wbits(wbits, True)) as g:
        return g.read()
