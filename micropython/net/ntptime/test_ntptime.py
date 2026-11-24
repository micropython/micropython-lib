import struct
import sys


class UDPSock:
    def __init__(self, reply):
        self._reply = reply

    def settimeout(self, timeout):
        pass

    def sendto(self, data, addr):
        pass

    def recv(self, n):
        return self._reply

    def close(self):
        pass


class FakeSocketMod:
    AF_INET = 2
    SOCK_DGRAM = 2

    def __init__(self, reply):
        self._reply = reply

    def getaddrinfo(self, host, port):
        return [(None, None, None, None, ("1.2.3.4", port))]

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


def _patch(reply):
    orig = ntptime.socket
    ntptime.socket = FakeSocketMod(reply)
    return orig


def test_time_ok():
    orig = _patch(ntp_msg())
    try:
        t = ntptime.time()
        assert isinstance(t, int)
    finally:
        ntptime.socket = orig


def test_time_short_raises():
    orig = _patch(b"short")
    try:
        try:
            ntptime.time()
            assert False, "expected OSError"
        except OSError as e:
            assert e.args == (-1,)
    finally:
        ntptime.socket = orig


def test_time_kod_stratum_raises():
    orig = _patch(ntp_msg(stratum=0))
    try:
        try:
            ntptime.time()
            assert False, "expected OSError"
        except OSError as e:
            assert e.args == (-1,)
    finally:
        ntptime.socket = orig


def test_time_zero_ts_raises():
    orig = _patch(ntp_msg(ts=0))
    try:
        try:
            ntptime.time()
            assert False, "expected OSError"
        except OSError as e:
            assert e.args == (-1,)
    finally:
        ntptime.socket = orig


def test_time_short_raises_ntp_error():
    orig = _patch(b"short")
    try:
        try:
            ntptime.time()
            assert False, "expected NTPError"
        except ntptime.NTPError as e:
            assert isinstance(e, OSError)
            assert e.args == (-1,)
    finally:
        ntptime.socket = orig


def test_unsupported_epoch_raises():
    orig_socket = _patch(ntp_msg())
    orig_gmtime = ntptime.gmtime
    ntptime.gmtime = lambda t: (2010, 1, 1, 0, 0, 0, 0, 0)
    try:
        try:
            ntptime.time()
            assert False, "expected UnsupportedEpochError"
        except ntptime.UnsupportedEpochError as e:
            assert isinstance(e, Exception)
            assert not isinstance(e, OSError)
            assert "Unsupported epoch: 2010" in str(e)
    finally:
        ntptime.gmtime = orig_gmtime
        ntptime.socket = orig_socket


test_time_ok()
test_time_short_raises()
test_time_kod_stratum_raises()
test_time_zero_ts_raises()
test_time_short_raises_ntp_error()
test_unsupported_epoch_raises()
