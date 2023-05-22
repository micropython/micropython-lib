# MicroPython SSD1305 OLED driver, I2C and SPI interfaces

from micropython import const
import framebuf

# register definitions
SET_CONTRAST = const(0x81)
SET_ENTIRE_ON = const(0xA4)
SET_NORM_INV = const(0xA6)
SET_DISP = const(0xAE)
SET_MEM_ADDR = const(0x20)
SET_COL_ADDR = const(0x21)
SET_PAGE_ADDR = const(0x22)
SET_DISP_START_LINE = const(0x40)
SET_LUT = const(0x91)
SET_SEG_REMAP = const(0xA0)
SET_MUX_RATIO = const(0xA8)
SET_MASTER_CONFIG = const(0xAD)
SET_COM_OUT_DIR = const(0xC0)
SET_COMSCAN_DEC = const(0xC8)
SET_DISP_OFFSET = const(0xD3)
SET_COM_PIN_CFG = const(0xDA)
SET_DISP_CLK_DIV = const(0xD5)
SET_AREA_COLOR = const(0xD8)
SET_PRECHARGE = const(0xD9)
SET_VCOM_DESEL = const(0xDB)
SET_CHARGE_PUMP = const(0x8D)


# Subclassing FrameBuffer provides support for graphics primitives
# http://docs.micropython.org/en/latest/pyboard/library/framebuf.html
class SSD1305(framebuf.FrameBuffer):
    def __init__(self, width, height, external_vcc, column_offset):
        self.width = width
        self.height = height
        self.external_vcc = external_vcc
        self.column_offset = column_offset if column_offset else 0
        self.pages = self.height // 8
        self.buffer = bytearray(self.pages * self.width)
        super().__init__(self.buffer, self.width, self.height, framebuf.MONO_VLSB)
        self.init_display()

    def init_display(self):
        for cmd in (
            SET_DISP | 0x00,  # off
            # timing and driving scheme
            SET_DISP_CLK_DIV,
            0x80,  # SET_DISP_CLK_DIV
            SET_SEG_REMAP | 0x01,  # column addr 127 mapped to SEG0 SET_SEG_REMAP
            SET_MUX_RATIO,
            self.height - 1,  # SET_MUX_RATIO
            SET_DISP_OFFSET,
            0x00,  # SET_DISP_OFFSET
            SET_MASTER_CONFIG,
            0x8E,  # Set Master Configuration
            SET_AREA_COLOR,
            0x05,  # Set Area Color Mode On/Off & Low Power Display Mode
            SET_MEM_ADDR,
            0x00,  # horizontal SET_MEM_ADDR ADD
            SET_DISP_START_LINE | 0x00,
            0x2E,  # SET_DISP_START_LINE ADD
            SET_COMSCAN_DEC,  # Set COM Output Scan Direction 64 to 1
            SET_COM_PIN_CFG,
            0x12,  # SET_COM_PIN_CFG
            SET_LUT,
            0x3F,
            0x3F,
            0x3F,
            0x3F,  # Current drive pulse width of BANK0, Color A, B, C
            SET_CONTRAST,
            0xFF,  # maximum SET_CONTRAST to maximum
            SET_PRECHARGE,
            0xD2,  # SET_PRECHARGE orig: 0xd9, 0x22 if self.external_vcc else 0xf1,
            SET_VCOM_DESEL,
            0x34,  # SET_VCOM_DESEL 0xdb, 0x30, $ 0.83* Vcc
            SET_NORM_INV,  # not inverted SET_NORM_INV
            SET_ENTIRE_ON,  # output follows RAM contents  SET_ENTIRE_ON
            SET_CHARGE_PUMP,
            0x10 if self.external_vcc else 0x14,  # SET_CHARGE_PUMP
            SET_DISP | 0x01,
        ):  # //--turn on oled panel
            self.write_cmd(cmd)
        self.fill(0)
        self.show()

    def poweroff(self):
        self.write_cmd(SET_DISP)

    def poweron(self):
        self.write_cmd(SET_DISP | 0x01)

    def contrast(self, contrast):
        self.write_cmd(SET_CONTRAST)
        self.write_cmd(contrast)

    def invert(self, invert):
        self.write_cmd(SET_NORM_INV | (invert & 1))

    def rotate(self, rotate):
        self.write_cmd(SET_COM_OUT_DIR | ((rotate & 1) << 3))
        self.write_cmd(SET_SEG_REMAP | (rotate & 1))

    def show(self):
        x0 = 0 + self.column_offset
        x1 = self.width - 1 + self.column_offset
        if self.width != 128:
            # narrow displays use centred columns
            col_offset = (128 - self.width) // 2
            x0 += col_offset
            x1 += col_offset
        self.write_cmd(SET_COL_ADDR)
        self.write_cmd(x0)
        self.write_cmd(x1)
        self.write_cmd(SET_PAGE_ADDR)
        self.write_cmd(0)
        self.write_cmd(self.pages - 1)
        self.write_data(self.buffer)


class SSD1305_I2C(SSD1305):
    def __init__(
        self,
        width,
        height,
        i2c,
        addr=0x3C,
        external_vcc=False,
        column_offset: int = None,
    ):
        self.i2c = i2c
        self.addr = addr
        self.temp = bytearray(2)
        self.write_list = [b"\x40", None]  # Co=0, D/C#=1
        super().__init__(width, height, external_vcc, column_offset)

    def write_cmd(self, cmd):
        self.temp[0] = 0x80  # Co=1, D/C#=0
        self.temp[1] = cmd
        self.i2c.writeto(self.addr, self.temp)

    def write_data(self, buf):
        self.write_list[1] = buf
        self.i2c.writevto(self.addr, self.write_list)


class SSD1305_SPI(SSD1305):
    def __init__(
        self, width, height, spi, dc, res, cs, external_vcc=False, column_offset=None
    ):
        self.rate = 10 * 1024 * 1024
        dc.init(dc.OUT, value=0)
        res.init(res.OUT, value=0)
        cs.init(cs.OUT, value=1)
        self.spi = spi
        self.dc = dc
        self.res = res
        self.cs = cs
        import time

        self.res(1)
        time.sleep_ms(1)
        self.res(0)
        time.sleep_ms(10)
        self.res(1)
        super().__init__(width, height, external_vcc, column_offset)

    def write_cmd(self, cmd):
        self.spi.init(baudrate=self.rate, polarity=0, phase=0)
        self.cs(1)
        self.dc(0)
        self.cs(0)
        self.spi.write(bytearray([cmd]))
        self.cs(1)

    def write_data(self, buf):
        self.spi.init(baudrate=self.rate, polarity=0, phase=0)
        self.cs(1)
        self.dc(1)
        self.cs(0)
        self.spi.write(buf)
        self.cs(1)
