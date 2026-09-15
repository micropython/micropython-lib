from ubinascii import *

if not "unhexlify" in globals():

    def unhexlify(data):
        if len(data) % 2 != 0:
            raise ValueError("Odd-length string")

        return bytes([int(data[i : i + 2], 16) for i in range(0, len(data), 2)])


b2a_hex = hexlify
a2b_hex = unhexlify

# ____________________________________________________________

_PAD = const("=")

# a2b = bytearray('\xff' * 256); for i, j in enumerate(b2a): a2b[ord(j)] = i
_TABLE_A2B_BASE64 = const(
    b"\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff"
    b"\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff"
    b"\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x3e\xff\xff\xff\x3f"
    b"\x34\x35\x36\x37\x38\x39\x3a\x3b\x3c\x3d\xff\xff\xff\xff\xff\xff"
    b"\xff\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e"
    b"\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\xff\xff\xff\xff\xff"
    b"\xff\x1a\x1b\x1c\x1d\x1e\x1f\x20\x21\x22\x23\x24\x25\x26\x27\x28"
    b"\x29\x2a\x2b\x2c\x2d\x2e\x2f\x30\x31\x32\x33\xff\xff\xff\xff\xff"
    b"\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff"
    b"\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff"
    b"\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff"
    b"\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff"
    b"\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff"
    b"\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff"
    b"\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff"
    b"\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff"
)


def a2b_base64(ascii):
    "Decode a line of base64 data."

    res = []
    quad_pos = 0
    leftchar = 0
    leftbits = 0
    last_char_was_a_pad = False

    for c in ascii:
        if c == 61:  # ord('=')
            if quad_pos > 2 or (quad_pos == 2 and last_char_was_a_pad):
                break  # stop on 'xxx=' or on 'xx=='
            last_char_was_a_pad = True
        else:
            n = _TABLE_A2B_BASE64[c]
            if n == 0xFF:
                continue  # ignore strange characters
            #
            # Shift it in on the low end, and see if there's
            # a byte ready for output.
            quad_pos = (quad_pos + 1) & 3
            leftchar = (leftchar << 6) | n
            leftbits += 6
            #
            if leftbits >= 8:
                leftbits -= 8
                res.append((leftchar >> leftbits).to_bytes(1, "big"))
                leftchar &= (1 << leftbits) - 1
            #
            last_char_was_a_pad = False
    else:
        if leftbits != 0:
            raise Exception("Incorrect padding")

    return b"".join(res)


# ____________________________________________________________

_TABLE_B2A_BASE64 = const("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/")


def b2a_base64(bin, newline=True):
    "Base64-code line of data."

    res = []

    leftchar = 0
    leftbits = 0
    for c in bin:
        # Shift into our buffer, and output any 6bits ready
        leftchar = (leftchar << 8) | c
        leftbits += 8
        res.append(_TABLE_B2A_BASE64[(leftchar >> (leftbits - 6)) & 0x3F])
        leftbits -= 6
        if leftbits >= 6:
            res.append(_TABLE_B2A_BASE64[(leftchar >> (leftbits - 6)) & 0x3F])
            leftbits -= 6
    #
    if leftbits == 2:
        res.append(_TABLE_B2A_BASE64[(leftchar & 3) << 4])
        res.append(_PAD)
        res.append(_PAD)
    elif leftbits == 4:
        res.append(_TABLE_B2A_BASE64[(leftchar & 0xF) << 2])
        res.append(_PAD)
    if newline:
        res.append("\n")
    return "".join(res).encode("ascii")
