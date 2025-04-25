#
# MicroPython driver for SD cards using SPI bus.
#
# Requires an SPI bus and a CS pin.  Provides readblocks and writeblocks
# methods so the device can be mounted as a filesystem.
#
# Example usage on pyboard:
#
#     import pyb, sdcard, os
#     sd = sdcard.SDCard(pyb.SPI(1), pyb.Pin.board.X5)
#     pyb.mount(sd, '/sd2')
#     os.listdir('/')
#
# Example usage on ESP8266:
#
#     import machine, sdcard, os
#     sd = sdcard.SDCard(machine.SPI(1), machine.Pin(15))
#     os.mount(sd, '/sd')
#     os.listdir('/')
#
# Note about the crc_function:
#     this is crc(seed: int, buf: buffer) -> int
#     If no crc16  function is provided, CRCs are not computed on data transfers.
#     If a crc16 is provided, the CRC  function of the SD card is enabled,
#     and data transfers both ways are protected by it
#

import micropython
from micropython import const
import time
import uctypes
from errno import ETIMEDOUT, EIO, ENODEV, EINVAL

crc7_be_syndrome_table = (
    b"\x00\x12$6HZl~\x90\x82\xb4\xa6\xd8\xca\xfc\xee2 \x16\x04zh^L\xa2\xb0\x86\x94\xea\xf8"
    b"\xce\xdcdv@R,>\x08\x1a\xf4\xe6\xd0\xc2\xbc\xae\x98\x8aVDr`\x1e\x0c:(\xc6\xd4\xe2\xf0"
    b"\x8e\x9c\xaa\xb8\xc8\xda\xec\xfe\x80\x92\xa4\xb6XJ|n\x10\x024&\xfa\xe8\xde\xcc\xb2\xa0"
    b'\x96\x84jxN\\"0\x06\x14\xac\xbe\x88\x9a\xe4\xf6\xc0\xd2<.\x18\ntfPB\x9e\x8c\xba\xa8'
    b"\xd6\xc4\xf2\xe0\x0e\x1c*8FTbp\x82\x90\xa6\xb4\xca\xd8\xee\xfc\x12\x006$ZH~l\xb0\xa2"
    b"\x94\x86\xf8\xea\xdc\xce 2\x04\x16hzL^\xe6\xf4\xc2\xd0\xae\xbc\x8a\x98vdR@>,\x1a\x08"
    b"\xd4\xc6\xf0\xe2\x9c\x8e\xb8\xaaDV`r\x0c\x1e(:JXn|\x02\x10&4\xda\xc8\xfe\xec\x92\x80"
    b'\xb6\xa4xj\\N0"\x14\x06\xe8\xfa\xcc\xde\xa0\xb2\x84\x96.<\n\x18ftBP\xbe\xac\x9a\x88\xf6'
    b"\xe4\xd2\xc0\x1c\x0e8*TFpb\x8c\x9e\xa8\xba\xc4\xd6\xe0\xf2"
)


def crc7(buf) -> int:
    crc = 0
    for b in buf:
        crc = crc7_be_syndrome_table[crc ^ b]
    return crc


def gb(bigval, b0, bn):
    # get numbered bits from a buf_to_int from, for example, the CSD
    return (bigval >> b0) & ((1 << (1 + bn - b0)) - 1)


_CMD_TIMEOUT = const(50)

_R1_IDLE_STATE = const(1 << 0)
# R1_ERASE_RESET = const(1 << 1)
_R1_ILLEGAL_COMMAND = const(1 << 2)
_R1_COM_CRC_ERROR = const(1 << 3)
# R1_ERASE_SEQUENCE_ERROR = const(1 << 4)
# R1_ADDRESS_ERROR = const(1 << 5)
# R1_PARAMETER_ERROR = const(1 << 6)
_TOKEN_CMD25 = const(0xFC)
_TOKEN_STOP_TRAN = const(0xFD)
_TOKEN_DATA = const(0xFE)
_HCS_BIT = const(1 << 30)  # for ACMD41


class SDCard:
    def __init__(self, spi, cs, baudrate=1320000, crc16_function=None):
        self.spi = spi
        self.cs = cs

        self.cmdbuf = bytearray(6)
        self.cmdbuf5 = memoryview(self.cmdbuf)[:5]  # for crc7 generation
        self.tokenbuf = bytearray(1)
        self.crcbuf = bytearray(2)
        self.crc16 = None  # during init
        # initialise the card
        self.init_card(baudrate)
        self.check_crcs(crc16_function)  # now set it up

    def check_crcs(self, crc16_function):
        self.crc16 = crc16_function
        result = self.cmd(
            59, 1 if crc16_function else 0, release=True
        )  # send CRC enable/disable command
        return result

    def init_spi(self, baudrate):
        try:
            master = self.spi.MASTER
        except AttributeError:
            # on ESP8266
            self.spi.init(baudrate=baudrate, phase=0, polarity=0)
        else:
            # on pyboard
            self.spi.init(master, baudrate=baudrate, phase=0, polarity=0)

    def _spiff(self):
        self.spi.write(b"\xff")

    def init_card(self, baudrate):
        # init CS pin
        self.cs.init(self.cs.OUT, value=1)

        # init SPI bus; use low data rate for initialisation
        self.init_spi(100000)

        # clock card at least 100 cycles with cs high (16 bytes = 128 cycles)
        # use explicit string here for small memory footprint
        self.spi.write(b"\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff")

        # CMD0: init card; should return _R1_IDLE_STATE (allow 5 attempts)
        for _ in range(5):
            if self.cmd(0, 0, 0x95) == _R1_IDLE_STATE:
                break
        else:
            raise OSError(ENODEV, "no SD card")

        # CMD8: determine card version
        r = self.cmd(8, 0x01AA, 4)  # probe version
        v2 = r == _R1_IDLE_STATE
        v1 = r == (_R1_IDLE_STATE | _R1_ILLEGAL_COMMAND)

        if not (v1 or v2):
            raise OSError(EIO, "couldn't determine SD card version")
        arg41 = _HCS_BIT if v2 else 0  # we support high capacity, on v2 cards
        for i in range(_CMD_TIMEOUT):  # loop on acmd41 to get
            self.cmd(55, 0)
            if (r := self.cmd(41, arg41)) == 0:
                break
            time.sleep_ms(5)
        if r != 0:
            raise OSError(ETIMEDOUT, "card type", "v2" if v2 else "v1")

        # get the number of sectors
        # CMD9: response R2 (R1 byte + 16-byte block read)
        if self.cmd(9, 0, 0, False) != 0:
            raise OSError(EIO, "no CSD response")
        csd = bytearray(16)
        self.readinto(csd)
        self.CSD = csd_int = int.from_bytes(
            csd, "big"
        )  # convert 16-byte CSD to a giant integer for bit extraction
        _gb = gb  # just for local binding
        # use bit numbers from SD card spec v9.0.0, table 5.3.2
        vers = _gb(csd_int, 126, 127)
        if vers == 1:  # CSD version 2.0
            self.sectors = (_gb(csd_int, 48, 69) + 1) * 1024
            self.cdv = 1
        elif vers == 0x00:  # CSD version 1.0 (old, <=2GB)
            c_size = _gb(csd_int, 62, 73)
            c_size_mult = _gb(csd_int, 47, 49)
            read_bl_len = _gb(csd_int, 80, 83)
            capacity = (c_size + 1) * (2 ** (c_size_mult + 2)) * (2**read_bl_len)
            self.sectors = capacity // 512
            self.cdv = 512  # converts bytes to sectors
        else:
            raise OSError(EIO, "CSD format unknown")
        # print('sectors', self.sectors)

        # CMD16: set block length to 512 bytes
        if self.cmd(16, 512) != 0:
            raise OSError(EIO, "can't set 512 block size")

        # set to high data rate now that it's initialised
        self.init_spi(baudrate)

    def cmd(self, cmd, arg, final=0, release=True, skip1=False):
        cs = self.cs  # prebind
        w = self.spi.write
        r = self.spi.readinto
        tb = self.tokenbuf
        spiff = self._spiff

        cs(0)  # select chip

        # create and send the command
        buf = self.cmdbuf
        buf[0] = 0x40 | cmd
        buf[1] = arg >> 24
        buf[2] = arg >> 16
        buf[3] = arg >> 8
        buf[4] = arg
        buf[5] = crc7(self.cmdbuf5) | 1
        w(buf)

        if skip1:
            r(tb, 0xFF)

        # wait for the response (response[7] == 0)
        for i in range(_CMD_TIMEOUT):
            r(tb, 0xFF)
            response = tb[0]
            # print(f"response: {response:02x}")

            if not (response & 0x80):
                # this could be a big-endian integer that we are getting here
                # if final<0 then store the first byte to tokenbuf and discard the rest
                if response & _R1_COM_CRC_ERROR:
                    cs(1)
                    spiff()
                    raise OSError(EIO, f"CRC err on cmd: {cmd:02d}")
                if final < 0:
                    r(tb, 0xFF)
                    final = -1 - final
                for j in range(final):
                    spiff()
                if release:
                    cs(1)
                    spiff()
                return response
            else:
                if i > (_CMD_TIMEOUT // 2):
                    time.sleep_ms(1)  # very slow response, give it time

        # timeout
        cs(1)
        spiff()
        raise OSError(ETIMEDOUT, "command:", cmd, "arg:", arg)

    def readinto(self, buf):
        cs = self.cs
        spiff = self._spiff

        cs(0)

        # read until start byte (0xff)
        for i in range(_CMD_TIMEOUT):
            self.spi.readinto(self.tokenbuf, 0xFF)
            if self.tokenbuf[0] == _TOKEN_DATA:
                break
            if i > _CMD_TIMEOUT // 2:
                time.sleep_ms(1)  # if response is slow, wait longer

        else:
            cs(1)
            raise OSError(ETIMEDOUT, "read timeout")

        self.spi.readinto(buf, 0xFF)

        # read checksum
        ck = self.spi.read(2, 0xFF)
        if self.crc16:
            crc = self.crc16(self.crc16(0, buf), ck)
            if crc != 0:
                raise OSError(EIO, f"bad data CRC: {crc:04x}")

        cs(1)
        spiff()

    def write(self, token, buf):
        cs = self.cs
        spiff = self._spiff
        r = self.spi.read
        w = self.spi.write

        cs(0)

        # send: start of block, data, checksum
        r(1, token)
        w(buf)
        if self.crc16:
            crc = self.crc16(0, buf)
            self.crcbuf[0] = crc >> 8
            self.crcbuf[1] = crc & 0xFF
            w(self.crcbuf)  # write checksum
        else:
            w(b"\xff\xff")
            # check the response
        if ((r(1, 0xFF)[0]) & 0x1F) != 0x05:
            cs(1)
            spiff()
            raise OSError(EIO, "write fail")

        # wait for write to finish
        while (r(1, 0xFF)[0]) == 0:
            pass

        cs(1)
        spiff()

    def write_token(self, token):
        self.cs(0)
        self.spi.read(1, token)
        self._spiff()
        # wait for write to finish
        while self.spi.read(1, 0xFF)[0] == 0x00:
            pass

        self.cs(1)
        self._spiff()

    @staticmethod
    def blocks(buf):
        nblocks, err = divmod(len(buf), 512)
        if not nblocks or err:
            raise OSError(EINVAL, "Buffer length is invalid")
        return nblocks

    def readblocks(self, block_num, buf):
        # workaround for shared bus, required for (at least) some Kingston
        # devices, ensure MOSI is high before starting transaction
        self._spiff()
        nblocks = self.blocks(buf)

        # CMD18: set read address for multiple blocks
        if self.cmd(18, block_num * self.cdv, release=False) != 0:
            # release the card
            self.cs(1)
            raise OSError(EIO)  # EIO
        mv = memoryview(buf)
        for offset in range(0, nblocks * 512, 512):
            self.readinto(mv[offset : offset + 512])

        if self.cmd(12, 0, skip1=True):
            raise OSError(EIO)  # EIO

    def writeblocks(self, block_num, buf):
        # workaround for shared bus, required for (at least) some Kingston
        # devices, ensure MOSI is high before starting transaction
        self._spiff()
        nblocks = self.blocks(buf)

        # CMD25: set write address for first block
        if self.cmd(25, block_num * self.cdv) != 0:
            raise OSError(EIO)  # EIO`
        # send the data
        mv = memoryview(buf)
        for offset in range(0, nblocks * 512, 512):
            self.write(_TOKEN_CMD25, mv[offset : offset + 512])
        self.write_token(_TOKEN_STOP_TRAN)

    def ioctl(self, op, arg):
        if op == 4:  # get number of blocks
            return self.sectors
        if op == 5:  # get block size in bytes
            return 512
