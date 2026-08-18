import struct
import sys


class UDPSock:
    def __init__(self, reply):
        self._reply = reply

    def settimeout(self, timeout):
        pass

    def sendto(self, data, addr):
        pass

    def recvfrom(self, n):
        return self._reply

    def close(self):
        pass


class FakeSocketMod:
    AF_INET = 2
    SOCK_DGRAM = 2

    def __init__(self, reply, ip="1.2.3.4"):
        self._reply = reply
        self._ip = ip

    def getaddrinfo(self, host, port):
        return [(None, None, None, None, (self._ip, port))]

    def socket(self, *a, **k):
        return UDPSock(self._reply)


sys.path.insert(0, "micropython/net/ntptime")
# ruff: noqa: E402
import ntptime


def ntp_msg(ts=3913056000, stratum=2):
    msg = bytearray(48)
    msg[1] = stratum
    struct.pack_into("!I", msg, 40, ts)
    return bytes(msg)


def _patch(reply, ip="1.2.3.4"):
    orig = ntptime.socket
    ntptime.socket = FakeSocketMod(reply, ip)
    return orig


def test_time_ok():
    orig = _patch((ntp_msg(), ("1.2.3.4", 123)))
    try:
        t = ntptime.time()
        assert isinstance(t, int)
    finally:
        ntptime.socket = orig


def test_time_short_raises():
    orig = _patch((b"short", ("1.2.3.4", 123)))
    try:
        try:
            ntptime.time()
            assert False, "expected OSError"
        except OSError as e:
            assert e.args == (-1,)
    finally:
        ntptime.socket = orig


def test_time_spoof_raises():
    orig = _patch((ntp_msg(), ("9.9.9.9", 123)))
    try:
        try:
            ntptime.time()
            assert False, "expected OSError"
        except OSError as e:
            assert e.args == (-1,)
    finally:
        ntptime.socket = orig


def test_time_kod_stratum_raises():
    orig = _patch((ntp_msg(stratum=0), ("1.2.3.4", 123)))
    try:
        try:
            ntptime.time()
            assert False, "expected OSError"
        except OSError as e:
            assert e.args == (-1,)
    finally:
        ntptime.socket = orig


def test_time_zero_ts_raises():
    orig = _patch((ntp_msg(ts=0), ("1.2.3.4", 123)))
    try:
        try:
            ntptime.time()
            assert False, "expected OSError"
        except OSError as e:
            assert e.args == (-1,)
    finally:
        ntptime.socket = orig


test_time_ok()
test_time_short_raises()
test_time_spoof_raises()
test_time_kod_stratum_raises()
test_time_zero_ts_raises()
