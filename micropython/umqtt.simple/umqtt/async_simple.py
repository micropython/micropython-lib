import struct
import asyncio


class MQTTException(Exception):
    pass


class MQTTClient:
    def __init__(
        self,
        client_id,
        server,
        port=0,
        user=None,
        password=None,
        keepalive=0,
        ssl=False,
        ssl_params={},
    ):
        if port == 0:
            port = 8883 if ssl else 1883
        self.client_id = client_id
        self.sock = None
        self.a_reader = None
        self.a_writer = None
        self.server = server
        self.port = port
        self.ssl = ssl
        self.ssl_params = ssl_params
        self.ssl_hostname = ssl_params.get("server_hostname")
        self.pid = 0
        self.cb = None
        self.user = user
        self.pswd = password
        self.keepalive = keepalive
        self.lw_topic = None
        self.lw_msg = None
        self.lw_qos = 0
        self.lw_retain = False

    async def _send_str(self, s):
        self.a_writer.write(struct.pack("!H", len(s)))
        self.a_writer.write(s)
        await self.a_writer.drain()

    async def _recv_len(self):
        n = 0
        sh = 0
        while 1:
            _b = await self.a_reader.read(1)
            b = _b[0]
            n |= (b & 0x7F) << sh
            if not b & 0x80:
                return n
            sh += 7

    def set_callback(self, f):
        self.cb = f

    def set_last_will(self, topic, msg, retain=False, qos=0):
        assert 0 <= qos <= 2
        assert topic
        self.lw_topic = topic
        self.lw_msg = msg
        self.lw_qos = qos
        self.lw_retain = retain

    async def connect(self, clean_session=True):
        self.a_reader, self.a_writer = await asyncio.open_connection(
            self.server, self.port, ssl=self.ssl, server_hostname=self.ssl_hostname
        )
        premsg = bytearray(b"\x10\0\0\0\0\0")
        msg = bytearray(b"\x04MQTT\x04\x02\0\0")

        sz = 10 + 2 + len(self.client_id)
        msg[6] = clean_session << 1
        if self.user is not None:
            sz += 2 + len(self.user) + 2 + len(self.pswd)
            msg[6] |= 0xC0
        if self.keepalive:
            assert self.keepalive < 65536
            msg[7] |= self.keepalive >> 8
            msg[8] |= self.keepalive & 0x00FF
        if self.lw_topic:
            sz += 2 + len(self.lw_topic) + 2 + len(self.lw_msg)
            msg[6] |= 0x4 | (self.lw_qos & 0x1) << 3 | (self.lw_qos & 0x2) << 3
            msg[6] |= self.lw_retain << 5

        i = 1
        while sz > 0x7F:
            premsg[i] = (sz & 0x7F) | 0x80
            sz >>= 7
            i += 1
        premsg[i] = sz

        self.a_writer.write(premsg[: i + 2])
        await self.a_writer.drain()
        self.a_writer.write(msg)
        await self.a_writer.drain()
        await self._send_str(self.client_id)
        if self.lw_topic:
            await self._send_str(self.lw_topic)
            await self._send_str(self.lw_msg)
        if self.user is not None:
            await self._send_str(self.user)
            await self._send_str(self.pswd)
        resp = await self.a_reader.read(4)
        assert resp[0] == 0x20 and resp[1] == 0x02
        if resp[3] != 0:
            raise MQTTException(resp[3])
        return resp[2] & 1

    async def disconnect(self):
        self.a_writer.write(b"\xe0\0")
        await self.a_writer.drain()
        self.a_writer.close()
        await self.a_writer.wait_closed()

    async def ping(self):
        self.a_writer.write(b"\xc0\0")
        await self.a_writer.drain()

    async def publish(self, topic, msg, retain=False, qos=0):
        pkt = bytearray(b"\x30\0\0\0")
        pkt[0] |= qos << 1 | retain
        sz = 2 + len(topic) + len(msg)
        if qos > 0:
            sz += 2
        assert sz < 2097152
        i = 1
        while sz > 0x7F:
            pkt[i] = (sz & 0x7F) | 0x80
            sz >>= 7
            i += 1
        pkt[i] = sz
        self.a_writer.write(pkt[: i + 1])
        await self.a_writer.drain()
        await self._send_str(topic)
        if qos > 0:
            self.pid += 1
            pid = self.pid
            struct.pack_into("!H", pkt, 0, pid)
            self.a_writer.write(pkt[:2])
            await self.a_writer.drain()
        self.a_writer.write(msg)
        await self.a_writer.drain()
        if qos == 1:
            while 1:
                op = await self.wait_msg()
                if op == 0x40:
                    sz = await self.a_reader.read(1)
                    assert sz == b"\x02"
                    rcv_pid = await self.a_reader.read(2)
                    rcv_pid = rcv_pid[0] << 8 | rcv_pid[1]
                    if pid == rcv_pid:
                        return
        elif qos == 2:
            assert 0

    async def subscribe(self, topic, qos=0):
        assert self.cb is not None, "Subscribe callback is not set"
        pkt = bytearray(b"\x82\0\0\0")
        self.pid += 1
        struct.pack_into("!BH", pkt, 1, 2 + 2 + len(topic) + 1, self.pid)
        self.a_writer.write(pkt)
        await self._send_str(topic)
        self.a_writer.write(qos.to_bytes(1, "little"))
        while 1:
            op = await self.wait_msg()
            if op == 0x90:
                resp = await self.a_reader.read(4)
                assert resp[1] == pkt[2] and resp[2] == pkt[3]
                if resp[3] == 0x80:
                    raise MQTTException(resp[3])
                return

    # Wait for a single incoming MQTT message and process it.
    # Subscribed messages are delivered to a callback previously
    # set by .set_callback() method. Other (internal) MQTT
    # messages processed internally.
    async def wait_msg(self):
        res = await self.a_reader.read(1)
        if res is None:
            return None
        if res == b"":
            raise OSError(-1)
        if res == b"\xd0":  # PINGRESP
            _sz = await self.a_reader.read(1)
            sz = _sz[0]
            assert sz == 0
            return None
        op = res[0]
        if op & 0xF0 != 0x30:
            return op
        sz = await self._recv_len()
        topic_len = await self.a_reader.read(2)
        topic_len = (topic_len[0] << 8) | topic_len[1]
        topic = await self.a_reader.read(topic_len)
        sz -= topic_len + 2
        if op & 6:
            pid = await self.a_reader.read(2)
            pid = pid[0] << 8 | pid[1]
            sz -= 2
        msg = await self.a_reader.read(sz)
        self.cb(topic, msg)
        if op & 6 == 2:
            pkt = bytearray(b"\x40\x02\0\0")
            struct.pack_into("!H", pkt, 2, pid)
            self.a_writer.write(pkt)
            await self.a_writer.drain()
        elif op & 6 == 4:
            assert 0
        return op

    # Checks whether a pending message from server is available.
    # If not, returns immediately with None. Otherwise, does
    # the same processing as wait_msg.
    async def check_msg(self):
        return await self.wait_msg()
