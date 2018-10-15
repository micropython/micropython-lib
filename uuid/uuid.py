import urandom
import ubinascii


def uuid4():
    r = bytearray([urandom.getrandbits(8) for _ in range(16)])
    r[7] = (r[7] & 0x0F) | 0x40
    r[9] = (r[9] & 0x3F) | 0x80
    h = ubinascii.hexlify(r).decode()
    return '-'.join((h[0:8], h[8:12], h[12:16], h[16:20], h[20:32]))
