import io
import sys


class Socket:
    def __init__(self, read_data=b""):
        self._write_buffer = io.BytesIO()
        self._read_buffer = io.BytesIO(read_data)

    def write(self, buf, length=None):
        if length is None:
            length = len(buf)
        self._write_buffer.write(buf[:length])

    def read(self, n):
        return self._read_buffer.read(n)

    def settimeout(self, timeout):
        pass

    def connect(self, addr):
        pass

    def setblocking(self, blocking):
        pass

    def close(self):
        pass


sys.path.insert(0, "micropython/umqtt.simple")
# ruff: noqa: E402
from umqtt.simple import MQTTClient, MQTTException
import umqtt.simple as umqtt_simple


def make_client(read_data):
    c = MQTTClient(b"cid", "127.0.0.1")
    c.sock = Socket(read_data)
    c.set_callback(lambda topic, msg: None)
    return c


def test_subscribe_short_topic():
    # Remaining Length = 5 + 4 = 9 -> single VBI byte 0x09, pid=1
    c = make_client(b"\x90\x03\x00\x01\x00")
    c.subscribe(b"abcd", qos=0)
    out = c.sock._write_buffer.getvalue()
    assert out[:2] == b"\x82\x09", out
    assert out[2:4] == b"\x00\x01", out
    assert out[4:6] == b"\x00\x04", out
    assert out[6:10] == b"abcd", out
    assert out[10:11] == b"\x00", out


def test_subscribe_long_topic():
    # Remaining Length = 5 + 123 = 128 -> VBI 0x80 0x01
    topic = b"a" * 123
    c = make_client(b"\x90\x03\x00\x01\x00")
    c.subscribe(topic, qos=0)
    out = c.sock._write_buffer.getvalue()
    assert out[:3] == b"\x82\x80\x01", out
    assert out[3:5] == b"\x00\x01", out
    assert out[5:7] == b"\x00\x7b", out
    assert out[7:130] == topic, out
    assert out[130:131] == b"\x00", out


def test_unsubscribe_long_topic():
    # Remaining Length = 4 + 123 = 127 -> still one VBI byte; use 124 for 128
    topic = b"a" * 124
    c = make_client(b"\xb0\x02\x00\x01")
    c.unsubscribe(topic)
    out = c.sock._write_buffer.getvalue()
    assert out[:3] == b"\xa2\x80\x01", out
    assert out[3:5] == b"\x00\x01", out
    assert out[5:7] == b"\x00\x7c", out
    assert out[7:131] == topic, out


class FakeSocketMod:
    def __init__(self, sock):
        self._sock = sock

    def socket(self, *a, **k):
        return self._sock

    def getaddrinfo(self, *a, **k):
        return [(None, None, None, None, ("127.0.0.1", 1883))]


def _patch_mqtt_socket(sock):
    orig = umqtt_simple.socket
    umqtt_simple.socket = FakeSocketMod(sock)
    return orig


def _restore_mqtt_socket(orig):
    umqtt_simple.socket = orig


def test_connect_ok():
    sock = Socket(b"\x20\x02\x00\x00")
    orig = _patch_mqtt_socket(sock)
    try:
        c = MQTTClient(b"cid", "127.0.0.1")
        assert c.connect() == 0
    finally:
        _restore_mqtt_socket(orig)


def test_connect_short_connack_raises():
    sock = Socket(b"")
    orig = _patch_mqtt_socket(sock)
    try:
        c = MQTTClient(b"cid", "127.0.0.1")
        try:
            c.connect()
            assert False, "expected MQTTException"
        except MQTTException as e:
            assert e.args == (-1,)
    finally:
        _restore_mqtt_socket(orig)


def test_connect_none_connack_raises():
    sock = Socket()
    sock.read = lambda n: None
    orig = _patch_mqtt_socket(sock)
    try:
        c = MQTTClient(b"cid", "127.0.0.1")
        try:
            c.connect()
            assert False, "expected MQTTException"
        except MQTTException as e:
            assert e.args == (-1,)
    finally:
        _restore_mqtt_socket(orig)


test_subscribe_short_topic()
test_subscribe_long_topic()
test_unsubscribe_long_topic()
test_connect_ok()
test_connect_short_connack_raises()
test_connect_none_connack_raises()
