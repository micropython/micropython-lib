import ubinascii as binascii
import usocket as socket
import ssl
import sys

sys.path[0] = ".."
import certifi.isrg  # micropython.org
import certifi.digicert  # github.com
import certifi.google
import certifi.amazon


ca_cert_chain = (
    certifi.isrg.CACERTS
    + certifi.digicert.CACERTS
    + certifi.google.CACERTS
    + certifi.amazon.CACERTS
)
sites = ["micropython.org", "github.com", "google.com", "amazon.com"]


def http_ping(addrss):
    s = socket.socket()
    ai = socket.getaddrinfo(addrss, 443)
    addr = ai[0][-1]
    s.connect(addr)
    s = ssl.wrap_socket(
        s, cert_reqs=ssl.CERT_REQUIRED, cadata=ca_cert_chain, server_hostname=addrss
    )
    s.write(b"GET / HTTP/1.0\r\n\r\n")
    print(s.read(17))
    s.close()


for site in sites:
    print(site)
    http_ping(site)
