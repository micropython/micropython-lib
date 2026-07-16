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

    def setblocking(self, blocking):
        pass

    def close(self):
        pass


sys.path.insert(0, "micropython/umqtt.simple")
# ruff: noqa: E402
from umqtt.simple import MQTTClient


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


test_subscribe_short_topic()
test_subscribe_long_topic()
test_unsubscribe_long_topic()
