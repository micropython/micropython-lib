"""
LSM6DSOX STMicro driver for MicroPython based on LSM9DS1:
Source repo: https://github.com/hoihu/projects/tree/master/raspi-hat

The MIT License (MIT)

Copyright (c) 2021 Damien P. George
Copyright (c) 2021-2023 Ibrahim Abdelkader <iabdalkader@openmv.io>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

Basic example usage::

    import time
    from lsm6dsox import LSM6DSOX

    from machine import Pin, SPI, I2C
    # Init in I2C mode.
    lsm = LSM6DSOX(I2C(0, scl=Pin(13), sda=Pin(12)))

    # Or init in SPI mode.
    #lsm = LSM6DSOX(SPI(5), cs=Pin(10))

    while (True):
        print('Accelerometer: x:{:>8.3f} y:{:>8.3f} z:{:>8.3f}'.format(*lsm.accel()))
        print('Gyroscope:     x:{:>8.3f} y:{:>8.3f} z:{:>8.3f}'.format(*lsm.gyro()))
        print("")
        time.sleep_ms(100)

"""

import array
from micropython import const
import time

_CTRL3_C = const(0x12)
_CTRL1_XL = const(0x10)
_CTRL8_XL = const(0x17)
_CTRL9_XL = const(0x18)

_CTRL2_G = const(0x11)
_CTRL7_G = const(0x16)

_OUTX_L_G = const(0x22)
_OUTX_L_XL = const(0x28)
_MLC_STATUS = const(0x38)
_MD1_CFG = const(0x5E)
_MD2_CFG = const(0x5F)

_PAGE_SEL = const(0x02)
_PAGE_ADDRESS = const(0x08)
_PAGE_VALUE = const(0x09)
_PAGE_RW = const(0x17)

_DEFAULT_ADDR = const(0x6A)
_WHO_AM_I_REG = const(0x0F)

_FUNC_CFG_ACCESS = const(0x01)
_FUNC_CFG_BANK_USER = const(0)
_FUNC_CFG_BANK_HUB = const(1)
_FUNC_CFG_BANK_EMBED = const(2)

_MLC0_SRC = const(0x70)
_MLC_INT1 = const(0x0D)
_TAP_CFG0 = const(0x56)

_EMB_FUNC_EN_A = const(0x04)
_EMB_FUNC_EN_B = const(0x05)
_EMB_FUNC_INT1 = const(0x0A)
_EMB_FUNC_INT2 = const(0x0E)
_EMB_FUNC_SRC = const(0x64)
_STEP_COUNTER_L = const(0x62)

_PEDO_DEB_STEPS_CONF = const(0x0184)

_PEDO_EN_MASK = const(0x08)
_PEDO_RST_STEP_MASK = const(0x80)
_PEDO_INT_MASK = const(0x08)
_INT_EMB_FUNC_MASK = const(0x02)


class LSM6DSOX:
    def __init__(
        self,
        bus,
        cs=None,
        address=_DEFAULT_ADDR,
        gyro_odr=104,
        accel_odr=104,
        gyro_scale=2000,
        accel_scale=4,
        ucf=None,
    ):
        """Initializes Gyro and Accelerator.
        accel_odr: (0, 1.6Hz, 3.33Hz, 6.66Hz, 12.5Hz, 26Hz, 52Hz, 104Hz, 208Hz, 416Hz, 888Hz)
        gyro_odr:  (0, 1.6Hz, 3.33Hz, 6.66Hz, 12.5Hz, 26Hz, 52Hz, 104Hz, 208Hz, 416Hz, 888Hz)
        gyro_scale:  (245dps, 500dps, 1000dps, 2000dps)
        accel_scale: (+/-2g, +/-4g, +/-8g, +-16g)
        ucf: MLC program to load.
        """
        self.bus = bus
        self.cs = cs
        self.address = address
        self._use_i2c = hasattr(self.bus, "readfrom_mem")

        if not self._use_i2c and cs is None:
            raise ValueError("A CS pin must be provided in SPI mode")

        # check the id of the Accelerometer/Gyro
        if self._read_reg(_WHO_AM_I_REG) != 108:
            raise OSError("No LSM6DS device was found at address 0x%x" % (self.address))

        # allocate scratch buffers for efficient conversions and memread op's
        self.scratch_int = array.array("h", [0, 0, 0])
        self.scratch_2b = bytearray(2)

        SCALE_GYRO = {250: 0, 500: 1, 1000: 2, 2000: 3}
        SCALE_ACCEL = {2: 0, 4: 2, 8: 3, 16: 1}
        # XL_HM_MODE = 0 by default. G_HM_MODE = 0 by default.
        ODR = {
            0: 0x00,
            1.6: 0x08,
            3.33: 0x09,
            6.66: 0x0A,
            12.5: 0x01,
            26: 0x02,
            52: 0x03,
            104: 0x04,
            208: 0x05,
            416: 0x06,
            888: 0x07,
        }

        gyro_odr = round(gyro_odr, 2)
        accel_odr = round(accel_odr, 2)

        # Sanity checks
        if gyro_odr not in ODR:
            raise ValueError("Invalid sampling rate: %d" % gyro_odr)
        if gyro_scale not in SCALE_GYRO:
            raise ValueError("invalid gyro scaling: %d" % gyro_scale)
        if accel_odr not in ODR:
            raise ValueError("Invalid sampling rate: %d" % accel_odr)
        if accel_scale not in SCALE_ACCEL:
            raise ValueError("invalid accelerometer scaling: %d" % accel_scale)

        # Soft-reset the device.
        self.reset()

        # Load and configure MLC if UCF file is provided
        if ucf is not None:
            self.load_mlc(ucf)

        # Set Gyroscope datarate and scale.
        # Note output from LPF2 second filtering stage is selected. See Figure 18.
        self._write_reg(_CTRL1_XL, (ODR[accel_odr] << 4) | (SCALE_ACCEL[accel_scale] << 2) | 2)

        # Enable LPF2 and HPF fast-settling mode, ODR/4
        self._write_reg(_CTRL8_XL, 0x09)

        # Set Gyroscope datarate and scale.
        self._write_reg(_CTRL2_G, (ODR[gyro_odr] << 4) | (SCALE_GYRO[gyro_scale] << 2) | 0)

        self.gyro_scale = 32768 / gyro_scale
        self.accel_scale = 32768 / accel_scale

    def _read_reg(self, reg, size=1):
        if self._use_i2c:
            buf = self.bus.readfrom_mem(self.address, reg, size)
        else:
            try:
                self.cs(0)
                self.bus.write(bytes([reg | 0x80]))
                buf = self.bus.read(size)
            finally:
                self.cs(1)
        if size == 1:
            return int(buf[0])
        return [int(x) for x in buf]

    def _write_reg(self, reg, val):
        if self._use_i2c:
            self.bus.writeto_mem(self.address, reg, bytes([val]))
        else:
            try:
                self.cs(0)
                self.bus.write(bytes([reg, val]))
            finally:
                self.cs(1)

    def _modify_bits(self, reg, clr_mask=0, set_mask=0):
        self._write_reg(reg, (self._read_reg(reg) & ~clr_mask) | set_mask)

    def _read_reg_into(self, reg, buf):
        if self._use_i2c:
            self.bus.readfrom_mem_into(self.address, reg, buf)
        else:
            try:
                self.cs(0)
                self.bus.write(bytes([reg | 0x80]))
                self.bus.readinto(buf)
            finally:
                self.cs(1)

    def _select_page(self, address, value=None):
        """
        Selects the embedded function page and reads/writes the value at the given address.
        If value is None, it reads the value at the address. Otherwise, it writes the value to the address.
        """
        msb = (address >> 8) & 0x0F  # MSB is the page number
        lsb = address & 0xFF  # LSB is the register address within the page

        self.set_mem_bank(_FUNC_CFG_BANK_EMBED)

        rw_bit = 0x20 if value is None else 0x40
        # Clear both read and write bits first, then set read (bit 5) or write (bit 6).
        self._modify_bits(_PAGE_RW, clr_mask=0x60, set_mask=rw_bit)

        # select page
        self._write_reg(_PAGE_SEL, (msb << 4) | 0x01)

        # set page addr
        self._write_reg(_PAGE_ADDRESS, lsb)

        val = None
        if value is None:
            # read value
            val = self._read_reg(_PAGE_VALUE)
        else:
            # write value
            self._write_reg(_PAGE_VALUE, value)

        # unset page write/read and page_sel
        self._write_reg(_PAGE_SEL, 0x01)
        self._modify_bits(_PAGE_RW, clr_mask=rw_bit)

        self.set_mem_bank(_FUNC_CFG_BANK_USER)
        return val

    def reset(self):
        self._modify_bits(_CTRL3_C, set_mask=0x1)
        for i in range(10):
            if (self._read_reg(_CTRL3_C) & 0x01) == 0:
                return
            time.sleep_ms(10)
        raise OSError("Failed to reset LSM6DS device.")

    def set_mem_bank(self, bank):
        self._modify_bits(_FUNC_CFG_ACCESS, clr_mask=0xC0, set_mask=(bank << 6))

    def set_embedded_functions(self, enable, emb_ab=None):
        self.set_mem_bank(_FUNC_CFG_BANK_EMBED)
        if enable:
            self._write_reg(_EMB_FUNC_EN_A, emb_ab[0])
            self._write_reg(_EMB_FUNC_EN_B, emb_ab[1])
        else:
            emb_a = self._read_reg(_EMB_FUNC_EN_A)
            emb_b = self._read_reg(_EMB_FUNC_EN_B)
            self._write_reg(_EMB_FUNC_EN_A, (emb_a & 0xC7))
            self._write_reg(_EMB_FUNC_EN_B, (emb_b & 0xE6))
            emb_ab = (emb_a, emb_b)

        self.set_mem_bank(_FUNC_CFG_BANK_USER)
        return emb_ab

    def load_mlc(self, ucf):
        # Load MLC config from file
        with open(ucf, "r") as ucf_file:
            for l in ucf_file:
                if l.startswith("Ac"):
                    v = [int(v, 16) for v in l.strip().split(" ")[1:3]]
                    self._write_reg(v[0], v[1])

        emb_ab = self.set_embedded_functions(False)

        # Disable I3C interface
        self._modify_bits(_CTRL9_XL, set_mask=0x01)

        # Enable Block Data Update
        self._modify_bits(_CTRL3_C, set_mask=0x40)

        # Route signals on interrupt pin 1
        self.set_mem_bank(_FUNC_CFG_BANK_EMBED)
        self._modify_bits(_MLC_INT1, clr_mask=0xFE)
        self.set_mem_bank(_FUNC_CFG_BANK_USER)

        # Configure interrupt pin mode
        self._modify_bits(_TAP_CFG0, set_mask=0x41)

        self.set_embedded_functions(True, emb_ab)

    def mlc_output(self):
        buf = None
        if self._read_reg(_MLC_STATUS) & 0x1:
            self._read_reg(0x1A, size=12)
            self.set_mem_bank(_FUNC_CFG_BANK_EMBED)
            buf = self._read_reg(_MLC0_SRC, 8)
            self.set_mem_bank(_FUNC_CFG_BANK_USER)
        return buf

    def pedometer_config(self, enable=True, debounce=10, int1_enable=False, int2_enable=False):
        """Configure the pedometer features."""
        self._select_page(_PEDO_DEB_STEPS_CONF, debounce)

        if int1_enable:
            self._modify_bits(_MD1_CFG, set_mask=_INT_EMB_FUNC_MASK)
        if int2_enable:
            self._modify_bits(_MD2_CFG, set_mask=_INT_EMB_FUNC_MASK)

        self.set_mem_bank(_FUNC_CFG_BANK_EMBED)

        self._modify_bits(_EMB_FUNC_EN_A, _PEDO_EN_MASK, enable and _PEDO_EN_MASK)
        self._modify_bits(_EMB_FUNC_INT1, _PEDO_INT_MASK, int1_enable and _PEDO_INT_MASK)
        self._modify_bits(_EMB_FUNC_INT2, _PEDO_INT_MASK, int2_enable and _PEDO_INT_MASK)

        self.set_mem_bank(_FUNC_CFG_BANK_USER)

    def pedometer_reset(self):
        """Reset the step counter."""
        self.set_mem_bank(_FUNC_CFG_BANK_EMBED)
        self._modify_bits(_EMB_FUNC_SRC, set_mask=_PEDO_RST_STEP_MASK)
        self.set_mem_bank(_FUNC_CFG_BANK_USER)

    def steps(self):
        """Return the number of detected steps."""
        self.set_mem_bank(_FUNC_CFG_BANK_EMBED)
        self._read_reg_into(_STEP_COUNTER_L, self.scratch_2b)
        self.set_mem_bank(_FUNC_CFG_BANK_USER)
        return self.scratch_2b[0] | (self.scratch_2b[1] << 8)

    def gyro(self):
        """Returns gyroscope vector in degrees/sec."""
        mv = memoryview(self.scratch_int)
        f = self.gyro_scale
        self._read_reg_into(_OUTX_L_G, mv)
        return (mv[0] / f, mv[1] / f, mv[2] / f)

    def accel(self):
        """Returns acceleration vector in gravity units (9.81m/s^2)."""
        mv = memoryview(self.scratch_int)
        f = self.accel_scale
        self._read_reg_into(_OUTX_L_XL, mv)
        return (mv[0] / f, mv[1] / f, mv[2] / f)
