"""
The MIT License (MIT)

Copyright (c) 2023 Arduino SA
Copyright (c) 2018 KPN (Jan Bogaerts)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""


import io
import struct


class CBOREncodeError(Exception):
    """Raised when an error occurs while serializing an object into a CBOR datastream."""


def encode_length(major_tag, length):
    if length < 24:
        return struct.pack(">B", major_tag | length)
    elif length < 256:
        return struct.pack(">BB", major_tag | 24, length)
    elif length < 65536:
        return struct.pack(">BH", major_tag | 25, length)
    elif length < 4294967296:
        return struct.pack(">BL", major_tag | 26, length)
    else:
        return struct.pack(">BQ", major_tag | 27, length)


def encode_semantic(encoder, tag, value):
    encoder.write(encode_length(0xC0, tag))
    encoder.encode(value)


def encode_float(encoder, value):
    # Handle special values efficiently
    import math

    if math.isnan(value):
        encoder.write(b"\xf9\x7e\x00")
    elif math.isinf(value):
        encoder.write(b"\xf9\x7c\x00" if value > 0 else b"\xf9\xfc\x00")
    else:
        encoder.write(struct.pack(">Bd", 0xFB, value))


def encode_int(encoder, value):
    # Big integers (2 ** 64 and over)
    if value >= 18446744073709551616 or value < -18446744073709551616:
        if value >= 0:
            major_type = 0x02
        else:
            major_type = 0x03
            value = -value - 1

        values = []
        while value > 0:
            value, remainder = divmod(value, 256)
            values.insert(0, remainder)

        payload = bytes(values)
        encode_semantic(encoder, major_type, payload)
    elif value >= 0:
        encoder.write(encode_length(0, value))
    else:
        encoder.write(encode_length(0x20, abs(value) - 1))


def encode_bytestring(encoder, value):
    encoder.write(encode_length(0x40, len(value)) + value)


def encode_bytearray(encoder, value):
    encode_bytestring(encoder, bytes(value))


def encode_string(encoder, value):
    encoded = value.encode("utf-8")
    encoder.write(encode_length(0x60, len(encoded)) + encoded)


def encode_map(encoder, value):
    encoder.write(encode_length(0xA0, len(value)))
    for key, val in value.items():
        encoder.encode(key)
        encoder.encode(val)


def encode_array(encoder, value):
    encoder.write(encode_length(0x80, len(value)))
    for item in value:
        encoder.encode(item)


def encode_boolean(encoder, value):
    encoder.write(b"\xf5" if value else b"\xf4")


def encode_none(encoder, value):
    encoder.write(b"\xf6")


cbor_encoders = {  # supported data types and the encoder to use.
    bytes: encode_bytestring,
    bytearray: encode_bytearray,
    str: encode_string,
    int: encode_int,
    float: encode_float,
    bool: encode_boolean,
    type(None): encode_none,
    list: encode_array,
    dict: encode_map,
}


class CBOREncoder(object):
    """
    Serializes objects to a byte stream using Concise Binary Object Representation.
    """

    def __init__(self, fp):
        self.fp = fp

    def _find_encoder(self, obj):
        return cbor_encoders[type(obj)]

    def write(self, data):
        """
        Write bytes to the data stream.
        :param data: the bytes to write
        """
        self.fp.write(data)

    def encode(self, obj):
        """
        Encode the given object using CBOR.
        :param obj: the object to encode
        """
        encoder = self._find_encoder(obj)
        if not encoder:
            raise CBOREncodeError("cannot serialize type %s" % type(obj))
        encoder(self, obj)


def dumps(obj, **kwargs):
    """
    Serialize an object to a bytestring.
    :param obj: the object to serialize
    :param kwargs: keyword arguments passed to :class:`~.CBOREncoder`
    :return: the serialized output
    :rtype: bytes
    """
    fp = io.BytesIO()
    dump(obj, fp, **kwargs)
    return fp.getvalue()


def dump(obj, fp, **kwargs):
    """
    Serialize an object to a file.
    :param obj: the object to serialize
    :param fp: a file-like object
    :param kwargs: keyword arguments passed to :class:`~.CBOREncoder`
    """
    CBOREncoder(fp, **kwargs).encode(obj)
