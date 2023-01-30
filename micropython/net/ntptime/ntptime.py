import utime

try:
    import usocket as socket
except:
    import socket
try:
    import ustruct as struct
except:
    import struct

# The NTP host can be configured at runtime by doing: ntptime.host = 'myhost.org'
host = "pool.ntp.org"
# The NTP socket timeout can be configured at runtime by doing: ntptime.timeout = 2
timeout = 1

TZ_HOST = "worldtimeapi.org"


def time():
    NTP_QUERY = bytearray(48)
    NTP_QUERY[0] = 0x1B
    addr = socket.getaddrinfo(host, 123)[0][-1]
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.settimeout(timeout)
        res = s.sendto(NTP_QUERY, addr)
        msg = s.recv(48)
    finally:
        s.close()
    val = struct.unpack("!I", msg[40:44])[0]

    EPOCH_YEAR = utime.gmtime(0)[0]
    if EPOCH_YEAR == 2000:
        # (date(2000, 1, 1) - date(1900, 1, 1)).days * 24*60*60
        NTP_DELTA = 3155673600
    elif EPOCH_YEAR == 1970:
        # (date(1970, 1, 1) - date(1900, 1, 1)).days * 24*60*60
        NTP_DELTA = 2208988800
    else:
        raise Exception("Unsupported epoch: {}".format(EPOCH_YEAR))

    return val - NTP_DELTA


def get_tz_offset(tz: str) -> int:
    tz = tz.strip()
    if "/" not in tz or len(tz) < 3:
        raise Exception("Unsupported timezone: {}. Example: asia/kolkata".format(tz))

    tz_offset = 0
    try:
        from urequests import get

        response = get("http://{}/api/timezone/{}".format(TZ_HOST, tz))
        tz_offset = response.json()["raw_offset"]
    except Exception:
        pass
    return tz_offset


def settime(tz: str = None):
    t = time()
    if tz:
        t += get_tz_offset(tz)
    import machine

    tm = utime.gmtime(t)
    machine.RTC().datetime((tm[0], tm[1], tm[2], tm[6] + 1, tm[3], tm[4], tm[5], 0))
