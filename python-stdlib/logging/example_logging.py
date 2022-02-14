#### Example 1 - basic stream log ####
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("test")
log.debug("Test message: %d(%s)", 100, "foobar")
log.info("Test message2: %d(%s)", 100, "foobar")
log.warning("Test message3: %d(%s)")
log.error("Test message4")
log.critical("Test message5")
logging.info("Test message6")

try:
    1 / 0
except:
    log.exception("Some trouble (%s)", "expected")


class MyHandler(logging.Handler):
    def emit(self, record):
        print("levelname=%(levelname)s name=%(name)s message=%(message)s" % record.__dict__)


logging.getLogger().addHandler(MyHandler())
logging.info("Test message7")


#### Example 2.1 - simple logger using basicConfig with explicit filename ####
import logging
logging.basicConfig(level=logging.INFO, filename="log.txt")
logging.info("Test message logged into a file")


#### Example 2.2 - simple logger using basicConfig with explicit stream ####
import logging
import sys
logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logging.info("Test message logged into sys.stderr")


#### Example 2.3 - simple logger using basicConfig with both stream and filename ####
import logging
logging.basicConfig(level=logging.INFO, stream=sys.stderr, filename="log.txt")
logging.info("Test message logged into a sys.stderr and a file")


#### Example 2.4 - simple logger using basicConfig with custom format string, %-style ####
import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", style="%")
logging.info("Test message logged into sys.stderr, (%d) %s", 42, "foo")


#### Example 2.4 - simple logger using basicConfig with custom format string, {-style ####
import logging
logging.basicConfig(level=logging.INFO, format="{asctime} {message}", style="{")
logging.info("Test message logged into sys.stderr")


#### Example 3 - Circular Log File with custom parameters ####
import logging
log = logging.getLogger("test")
f = logging.Formatter(fmt="%(asctime)s %(uptime)s %(levelname)s %(message)s")
h = logging.CircularFileHandler('log.txt', maxsize=512_000)   # 512 kB log file
h.setFormatter(f)
log.addHandler(h)

log.info("Test message 1 logged into a file")
log.info("Test message 2 logged into a file")


#### Example 4 - log to a custom log receiver at 198.51.100.1 UDP port 3000 ####
import logging
log = logging.getLogger("test")
log.addHandler(logging.SocketHandler('198.51.100.1', 3000))
log.info("Test message 1 logged into a UDP socket")
log.info("Test message 2 logged into a UDP socket")


#### Example 5 - log to a custom log receiver at 198.51.100.1 TCP port 3000 ####
import logging
import socket
log = logging.getLogger("test")
log.addHandler(logging.SocketHandler('198.51.100.1', 3000, socktype=socket.SOCK_STREAM))
log.info("Test message 1 logged into a TCP socket")
log.info("Test message 2 logged into a TCP socket")


#### Example 6 - log to a syslog server at 198.51.100.1 using UDP transport ####
import logging
log = logging.getLogger("test")
log.addHandler(logging.SysLogHandler('198.51.100.1'))
log.info("Test message 1 logged to a syslog server over UDP")
log.info("Test message 2 logged to a syslog server over UDP")


#### Example 7 - log to a syslog server at 198.51.100.1 using TCP transport ####
import logging
import socket
import network

log_defaults = {
    "ip": network.WLAN(network.STA_IF).ifconfig()[0],
    "hostname": network.WLAN(network.STA_IF).config("dhcp_hostname"),
}

log = logging.getLogger("test")
f = logging.Formatter(fmt=logging.SYSLOG_FORMAT, defaults=log_defaults)
h = logging.SysLogHandler('198.51.100.1', socktype=socket.SOCK_STREAM)
h.setFormatter(f)
log.addHandler(h)

log.info("Test message 1 logged to a syslog server over TCP")
log.info("Test message 2 logged to a syslog server over TCP")


#### Example 8 - Circular Log File with custom parameters and {-style formatting string ####
import logging
log = logging.getLogger("test")
f = logging.Formatter(fmt="{asctime} {uptime} {message}", style="{")
h = logging.CircularFileHandler('log.txt', maxsize=512_000)
h.setFormatter(f)
log.addHandler(h)

log.info("Test message 1 logged into a file")
log.info("Test message 2 logged into a file")
