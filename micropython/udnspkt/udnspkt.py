import struct


def write_fqdn(buf, name):
    data = bytearray()
    for part in name.split("."):
        data.append(len(part))
        data.extend(part.encode("ascii"))
    data.append(0)
    buf.write(data)


def skip_fqdn(buf):
    while True:
        # Label size
        size = (buf.read(1) or b"\x00")[0]
        if not size:
            # Truncated packet or last label
            return
        # Ignore compressed response pointer
        if size >= 0xC0:
            buf.read(1)
            return
        # Skip label
        buf.read(size)


def make_req(buf, fqdn, is_ipv6):
    # As per RFC1035, §4.1.1
    # ID 0, Standard query, just one question entry
    buf.write(b"\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00")
    # §4.1.3
    write_fqdn(buf, fqdn)
    buf.write(b"\x00\x1c\x00\x01" if is_ipv6 else b"\x00\x01\x00\x01")


def parse_resp(buf, is_ipv6):
    # As per RFC1035, §4.1.1
    _, flags, _, acnt, *_ = struct.unpack(">6H", buf.read(6 * 2))
    # Bit 15 indicates it's a response, and bits 3..0 is the response code.
    if flags & 0x800F != 0x8000:
        raise ValueError(flags)
    skip_fqdn(buf)
    buf.read(4)
    for _ in range(acnt):
        skip_fqdn(buf)
        t, *_, rlen = struct.unpack(">HHIH", buf.read(4 + (3 * 2)))
        rval = buf.read(rlen)
        if t == (0x1C if is_ipv6 else 0x01):
            return rval
