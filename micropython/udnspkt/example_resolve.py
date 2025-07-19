import io
import socket

import udnspkt


s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
dns_addr = socket.getaddrinfo("127.0.0.1", 53)[0][-1]


def resolve(domain, is_ipv6):
    buf = io.BytesIO(48)
    udnspkt.make_req(buf, "google.com", is_ipv6)
    v = buf.getvalue()
    print("query: ", v)
    s.sendto(v, dns_addr)

    resp = s.recv(1024)
    print("resp:", resp)
    buf = io.BytesIO(resp)

    addr = udnspkt.parse_resp(buf, is_ipv6)
    print("bin addr:", addr)
    print("addr:", socket.inet_ntop(socket.AF_INET6 if is_ipv6 else socket.AF_INET, addr))


resolve("google.com", False)
print()
resolve("google.com", True)
