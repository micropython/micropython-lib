def write_fqdn(buf, name):
    parts = name.split(".")
    for p in parts:
        buf.writebin("B", len(p))
        buf.write(p)
    buf.writebin("B", 0)


def skip_fqdn(buf):
    while True:
        sz = buf.readbin("B")
        if not sz:
            break
        if sz >= 0xC0:
            buf.readbin("B")
            break
        buf.read(sz)


def make_req(buf, fqdn, is_ipv6):
    typ = 1  # A
    if is_ipv6:
        typ = 28  # AAAA

    buf.writebin(">H", 0)
    buf.writebin(">H", 0x100)
    # q count
    buf.writebin(">H", 1)
    buf.writebin(">H", 0)
    # squashed together
    buf.writebin(">I", 0)

    write_fqdn(buf, fqdn)
    buf.writebin(">H", typ)
    buf.writebin(">H", 1)  # Class


def parse_resp(buf, is_ipv6):
    typ = 1  # A
    if is_ipv6:
        typ = 28  # AAAA

    buf.readbin(">H")  # id
    flags = buf.readbin(">H")
    assert flags & 0x8000
    buf.readbin(">H")  # qcnt
    acnt = buf.readbin(">H")
    buf.readbin(">H")  # nscnt
    buf.readbin(">H")  # addcnt

    skip_fqdn(buf)
    buf.readbin(">H")
    buf.readbin(">H")

    for i in range(acnt):
        # print("Resp #%d" % i)
        # v = read_fqdn(buf)
        # print(v)
        skip_fqdn(buf)
        t = buf.readbin(">H")  # Type
        buf.readbin(">H")  # Class
        buf.readbin(">I")  # TTL
        rlen = buf.readbin(">H")
        rval = buf.read(rlen)

        if t == typ:
            return rval
