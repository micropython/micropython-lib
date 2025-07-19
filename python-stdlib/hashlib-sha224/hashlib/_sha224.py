# MIT license; Copyright (c) 2023 Jim Mussared
# Originally ported from CPython by Paul Sokolovsky

from ._sha256 import sha256


class sha224(sha256):
    digest_size = digestsize = 28
    _iv = [
        0xC1059ED8,
        0x367CD507,
        0x3070DD17,
        0xF70E5939,
        0xFFC00B31,
        0x68581511,
        0x64F98FA7,
        0xBEFA4FA4,
    ]
