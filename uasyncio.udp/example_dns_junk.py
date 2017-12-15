# This example is intended to run with dnsmasq running on localhost
# (Ubuntu comes configured like that by default). Dnsmasq, receiving
# some junk, is still kind to reply something back, which we employ
# here.
import uasyncio
import uasyncio.udp
import usocket

def udp_req(addr):
    s = uasyncio.udp.socket()
    print(s)
    yield from uasyncio.udp.sendto(s, b"!eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee", addr)
    try:
        resp = yield from uasyncio.wait_for(uasyncio.udp.recv(s, 1024), 1)
        print(resp)
    except uasyncio.TimeoutError:
        print("timed out")


import logging
logging.basicConfig(level=logging.INFO)

addr = usocket.getaddrinfo("127.0.0.1", 53)[0][-1]
loop = uasyncio.get_event_loop()
loop.run_until_complete(udp_req(addr))
loop.close()
