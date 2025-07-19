"""
The MIT License (MIT)

Copyright (c) 2023 Arduino SA

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

Basic example usage:

import time
from bmm150 import BMM150
from machine import Pin, SPI, I2C

# Init in I2C mode.
imu = BMM150(I2C(1, scl=Pin(15), sda=Pin(14)))

# Or init in SPI mode.
# TODO: Not supported yet.
# imu = BMM150(SPI(5), cs=Pin(10))

while (True):
    print('magnetometer: x:{:>8.3f} y:{:>8.3f} z:{:>8.3f}'.format(*imu.magnet()))
    time.sleep_ms(100)
"""

import array
import time
from micropython import const

_DEFAULT_ADDR = const(0x10)
_CHIP_ID = const(0x40)
_DATA = const(0x42)
_POWER = const(0x4B)
_OPMODE = const(0x4C)
_INT_STATUS = const(0x4A)
_TRIM_X1 = const(0x5D)
_TRIM_Y1 = const(0x5E)
_TRIM_Z4_LSB = const(0x62)
_TRIM_Z2_LSB = const(0x68)
_XYAXES_FLIP = const(-4096)
_ZHAXES_FLIP = const(-16384)
_ODR = const((10, 2, 6, 8, 15, 20, 25, 30))


class BMM150:
    def __init__(
        self,
        bus,
        cs=None,
        address=_DEFAULT_ADDR,
        magnet_odr=30,
    ):
        """Initalizes the Magnetometer.
        bus: IMU bus
        address: I2C address (in I2C mode).
        cs: SPI CS pin (in SPI mode).
        magnet_odr: (2, 6, 8, 10, 15, 20, 25, 30)
        """
        self.bus = bus
        self.cs = cs
        self.address = address
        self._use_i2c = hasattr(self.bus, "readfrom_mem")

        # Sanity checks
        if not self._use_i2c:
            raise ValueError("SPI mode is not supported")
        if magnet_odr not in _ODR:
            raise ValueError("Invalid sampling rate: %d" % magnet_odr)

        # Perform soft reset, and power on.
        self._write_reg(_POWER, 0x83)
        time.sleep_ms(10)

        if self._read_reg(_CHIP_ID) != 0x32:
            raise OSError("No BMM150 device was found at address 0x%x" % (self.address))

        # Configure the device.
        # ODR | OP: Normal mode
        self._write_reg(_OPMODE, _ODR.index(magnet_odr) << 3)

        # Read trim registers.
        trim_x1y1 = self._read_reg(_TRIM_X1, 2)
        trim_xyz_data = self._read_reg(_TRIM_Z4_LSB, 4)
        trim_xy1xy2 = self._read_reg(_TRIM_Z2_LSB, 10)

        self.trim_x1 = trim_x1y1[0]
        self.trim_y1 = trim_x1y1[1]
        self.trim_x2 = trim_xyz_data[2]
        self.trim_y2 = trim_xyz_data[3]
        self.trim_z1 = (trim_xy1xy2[3] << 8) | trim_xy1xy2[2]
        self.trim_z2 = (trim_xy1xy2[1] << 8) | trim_xy1xy2[0]
        self.trim_z3 = (trim_xy1xy2[7] << 8) | trim_xy1xy2[6]
        self.trim_z4 = (trim_xyz_data[1] << 8) | trim_xyz_data[0]
        self.trim_xy1 = trim_xy1xy2[9]
        self.trim_xy2 = trim_xy1xy2[8]
        self.trim_xyz1 = ((trim_xy1xy2[5] & 0x7F) << 8) | trim_xy1xy2[4]

        # Allocate scratch buffer.
        self.scratch = memoryview(array.array("h", [0, 0, 0, 0]))

    def _read_reg(self, reg, size=1):
        buf = self.bus.readfrom_mem(self.address, reg, size)
        if size == 1:
            return int(buf[0])
        return buf

    def _read_reg_into(self, reg, buf):
        self.bus.readfrom_mem_into(self.address, reg, buf)

    def _write_reg(self, reg, val):
        self.bus.writeto_mem(self.address, reg, bytes([val]))

    def _compensate_x(self, raw, hall):
        """Compensation equation ported from C driver"""
        x = 0
        if raw != _XYAXES_FLIP:
            x0 = self.trim_xyz1 * 16384 / hall
            x = x0 - 16384
            x1 = (self.trim_xy2) * (x**2 / 268435456)
            x2 = x1 + x * (self.trim_xy1) / 16384
            x3 = (self.trim_x2) + 160
            x4 = raw * ((x2 + 256) * x3)
            x = ((x4 / 8192) + (self.trim_x1 * 8)) / 16
        return x

    def _compensate_y(self, raw, hall):
        """Compensation equation ported from C driver"""
        y = 0
        if raw != _XYAXES_FLIP:
            y0 = self.trim_xyz1 * 16384 / hall
            y = y0 - 16384
            y1 = self.trim_xy2 * (y**2 / 268435456)
            y2 = y1 + y * self.trim_xy1 / 16384
            y3 = self.trim_y2 + 160
            y4 = raw * ((y2 + 256) * y3)
            y = ((y4 / 8192) + (self.trim_y1 * 8)) / 16
        return y

    def _compensate_z(self, raw, hall):
        """Compensation equation ported from C driver"""
        z = 0
        if raw != _ZHAXES_FLIP:
            z0 = raw - self.trim_z4
            z1 = hall - self.trim_xyz1
            z2 = self.trim_z3 * z1
            z3 = (self.trim_z1 * hall) / 32768
            z4 = self.trim_z2 + z3
            z5 = (z0 * 131072) - z2
            z = (z5 / (z4 * 4)) / 16
        return z

    def magnet_raw(self):
        for i in range(10):
            self._read_reg_into(_DATA, self.scratch)
            if self.scratch[3] & 0x1:
                return (
                    self.scratch[0] >> 3,
                    self.scratch[1] >> 3,
                    self.scratch[2] >> 1,
                    self.scratch[3] >> 2,
                )
            time.sleep_ms(30)
        raise OSError("Data not ready")

    def magnet(self):
        """Returns magnetometer vector."""
        x, y, z, h = self.magnet_raw()
        return (self._compensate_x(x, h), self._compensate_y(y, h), self._compensate_z(z, h))
