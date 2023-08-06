# MIT license; Copyright (c) 2023 Jim Mussared
# Originally ported from CPython by Paul Sokolovsky

from ._sha512 import sha512


class sha384(sha512):
    digest_size = digestsize = 48
    _iv = [
        0xCBBB9D5DC1059ED8,
        0x629A292A367CD507,
        0x9159015A3070DD17,
        0x152FECD8F70E5939,
        0x67332667FFC00B31,
        0x8EB44A8768581511,
        0xDB0C2E0D64F98FA7,
        0x47B5481DBEFA4FA4,
    ]
