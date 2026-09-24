class LegacyFileTransfer:
    def __init__(self):
        self.opbuf = bytearray(82)
        self.opptr = 0
        self.op = 0

    def handle(self, buf, sock):
        if self.op == 2:
            import struct

            ret = self.file.readinto(memoryview(self.filebuf)[2:])
            memoryview(self.filebuf)[0:2] = struct.pack("<h", ret)
            sock.ioctl(9, 2)
            sock.write(memoryview(self.filebuf)[0 : (2 + ret)])
            if ret == 0:
                sock.write(b"WB\x00\x00")
                self.op = 0
                self.filebuf = None
            sock.ioctl(9, 1)
            return
        self.opbuf[self.opptr] = buf[0]
        self.opptr += 1
        if self.opptr != 82:  # or bytes(buf[0:2]) != b"WA":
            return
        self.opptr = 0
        sock.ioctl(9, 2)
        sock.write(b"WB\x00\x00")
        sock.ioctl(9, 1)
        type = self.opbuf[2]
        if type == 2:  # GET_FILE
            self.op = type
            name = self.opbuf[18:82].rstrip(b"\x00")
            self.filebuf = bytearray(2 + 256)
            self.file = open(name.decode(), "rb")
        elif type == 1:  # PUT_FILE
            import struct

            name = self.opbuf[18:82].rstrip(b"\x00")
            size = struct.unpack("<I", self.opbuf[12:16])[0]
            filebuf = bytearray(512)
            with open(name.decode(), "wb") as file:
                while size > 0:
                    ret = sock.readinto(filebuf)
                    if ret is None:
                        continue
                    if ret > 0:
                        file.write(memoryview(filebuf)[0:ret])
                        size -= ret
                    elif ret < 0:
                        break
            sock.ioctl(9, 2)
            sock.write(b"WB\x00\x00")
            sock.ioctl(9, 1)
