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

Modified to use 'maximum fifo' configuration and optimised for speed
by Owen Carter, Feb 2026

Homepage: https://codeberg.org/easytarget/bmi270-micropython/

Basic example usage::

    import time
    from bmi270 import BMI270
    from machine import Pin, I2C

    # Init in I2C mode, adjust pins as needed
    i2c = I2C(1, scl=Pin(32), sda=Pin(31))
    imu = BMI270(i2c)

    while (True):
        print('Accelerometer: x:{:>6.3f}  y:{:>6.3f}  z:{:>6.3f}'.format(*imu.accel()))
        print('Gyroscope:     x:{:>6.3f}  y:{:>6.3f}  z:{:>6.3f}'.format(*imu.gyro()))
        print('Temperature: {:>4.1f}'.format(imu.temperature()))
        print("")
        time.sleep_ms(100)

"""

import array
from time import sleep_ms, sleep_us

from micropython import const

# I2C address
_DEFAULT_ADDR = const(0x68)

# Core device registers (8 bit)
_CHIP_ID = const(0x00)
_DATA_8 = const(0x0C)
_DATA_14 = const(0x12)
_EVENT = const(0x1B)
_INTERNAL_STATUS = const(0x21)
_TEMP_REG = const(0x22)
_ACC_CONF = const(0x40)
_ACC_RANGE = const(0x41)
_GYR_CONF = const(0x42)
_GYR_RANGE = const(0x43)
_INIT_CTRL = const(0x59)
_INIT_ADDR_0 = const(0x5B)
_INIT_ADDR_1 = const(0x5C)
_INIT_DATA = const(0x5E)
_PWR_CONF = const(0x7C)
_PWR_CTRL = const(0x7D)
_CMD = const(0x7E)

# Config for the maximum fifo profile (328 bytes)
_CONFIG_DATA = const(
    b"\xc8\x2e\x00\x2e\x80\x2e\x1a\x00\xc8\x2e\x00\x2e\xc8\x2e\x00\x2e\xc8\x2e\x00"
    b"\x2e\xc8\x2e\x00\x2e\xc8\x2e\x00\x2e\xc8\x2e\x00\x2e\x90\x32\x21\x2e\x59\xf5"
    b"\x10\x30\x21\x2e\x6a\xf5\x1a\x24\x22\x00\x80\x2e\x3b\x00\xc8\x2e\x44\x47\x22"
    b"\x00\x37\x00\xa4\x00\xff\x0f\xd1\x00\x07\xad\x80\x2e\x00\xc1\x80\x2e\x00\xc1"
    b"\x80\x2e\x00\xc1\x80\x2e\x00\xc1\x80\x2e\x00\xc1\x80\x2e\x00\xc1\x80\x2e\x00"
    b"\xc1\x80\x2e\x00\xc1\x80\x2e\x00\xc1\x80\x2e\x00\xc1\x80\x2e\x00\xc1\x00\x00"
    b"\x00\x00\x00\x00\x11\x24\xfc\xf5\x80\x30\x40\x42\x50\x50\x00\x30\x12\x24\xeb"
    b"\x00\x03\x30\x00\x2e\xc1\x86\x5a\x0e\xfb\x2f\x21\x2e\xfc\xf5\x13\x24\x63\xf5"
    b"\xe0\x3c\x48\x00\x22\x30\xf7\x80\xc2\x42\xe1\x7f\x3a\x25\xfc\x86\xf0\x7f\x41"
    b"\x33\x98\x2e\xc2\xc4\xd6\x6f\xf1\x30\xf1\x08\xc4\x6f\x11\x24\xff\x03\x12\x24"
    b"\x00\xfc\x61\x09\xa2\x08\x36\xbe\x2a\xb9\x13\x24\x38\x00\x64\xbb\xd1\xbe\x94"
    b"\x0a\x71\x08\xd5\x42\x21\xbd\x91\xbc\xd2\x42\xc1\x42\x00\xb2\xfe\x82\x05\x2f"
    b"\x50\x30\x21\x2e\x21\xf2\x00\x2e\x00\x2e\xd0\x2e\xf0\x6f\x02\x30\x02\x42\x20"
    b"\x26\xe0\x6f\x02\x31\x03\x40\x9a\x0a\x02\x42\xf0\x37\x05\x2e\x5e\xf7\x10\x08"
    b"\x12\x24\x1e\xf2\x80\x42\x83\x84\xf1\x7f\x0a\x25\x13\x30\x83\x42\x3b\x82\xf0"
    b"\x6f\x00\x2e\x00\x2e\xd0\x2e\x12\x40\x52\x42\x00\x2e\x12\x40\x52\x42\x3e\x84"
    b"\x00\x40\x40\x42\x7e\x82\xe1\x7f\xf2\x7f\x98\x2e\x6a\xd6\x21\x30\x23\x2e\x61"
    b"\xf5\xeb\x2c\xe1\x6f"
)


class BMI270:
    ACCEL_SCALE = (2, 4, 8, 16)
    GYRO_SCALE = (2000, 1000, 500, 250, 125)
    ODR = (0.78, 1.5, 3.1, 6.25, 12.5, 25, 50, 100, 200, 400, 800, 1200)

    def __init__(
        self,
        i2c,
        address=_DEFAULT_ADDR,
        gyro_odr=100,
        gyro_scale=2000,
        accel_odr=100,
        accel_scale=4,
        force_reset=False,
        bmm_magnet=None,
    ):
        """Initializes Device, Gyro and Accelerometer.
        i2c: machine.I2C bus object
        address: I2C address
        gyro_odr:  (0.78, 1.5Hz, 3.1Hz, 6.25Hz, 12.5Hz, 25Hz, 50Hz, 100Hz, 200Hz, 400Hz, 800Hz, 1600Hz)
        gyro_scale:  (125dps, 250dps, 500dps, 1000dps, 2000dps)
        accel_odr: (0.78, 1.5Hz, 3.1Hz, 6.25Hz, 12.5Hz, 25Hz, 50Hz, 100Hz, 200Hz, 400Hz, 800Hz, 1600Hz)
        accel_scale: (+/-2g, +/-4g, +/-8g, +-16g)
        force_reset: Forces a reset and reinitialisation of the device
        bmm_magnet:  allows passing of a magnetometer device, not used in practice
        """
        self.bus = i2c
        self.bmm_magnet = bmm_magnet
        self.address = address
        self.powersave = True
        self.reset_flag = False

        # Self checks
        if self._read_reg(_CHIP_ID) != 0x24:
            raise OSError("No BMI270 device was found at address 0x%x" % (self.address))
        # check power on reset and error flags
        needs_reset = False
        if self._read_reg(_EVENT) & 0x01:  # power on reset
            needs_reset = True
        if self._read_reg(_INTERNAL_STATUS) != 0x01:  # init not ok
            needs_reset = True
        # reset and upload config as needed
        if force_reset or needs_reset:
            self._reset()
        # apply sensor settings
        self.sensor_settings(gyro_odr, gyro_scale, accel_odr, accel_scale)
        # Allocate scratch buffers.
        self._scratch = memoryview(array.array("h", [0, 0, 0]))
        self._word = memoryview(array.array("h", [0]))

    def _reset(self):
        """Soft reset the device and upload config"""
        # This will leave the device in full power mode
        self._write_reg(_CMD, 0xB6)
        sleep_ms(50)
        # Disable power save mode.
        self._write_reg(_PWR_CONF, 0x00)
        self.powersave = False
        # Prepare config load.
        self._write_reg(_INIT_CTRL, 0x00)
        # Load config data.
        self._write_burst(_CONFIG_DATA)
        # Finish config load.
        self._write_reg(_INIT_CTRL, 0x01)
        sleep_ms(20)
        # Check correct initialization status.
        if not self._poll_reg(_INTERNAL_STATUS, 0x01):
            raise OSError("Init configuration load failed")
        # FIFO Reset
        self._write_reg(_CMD, 0xB0)
        # Disable adv_power_save | Enable fifo_self_wakeup.
        self._write_reg(_PWR_CONF, 0x02)
        # Enable accel, gyro and temperature data.
        self._write_reg(_PWR_CTRL, 0x0E)
        self.reset_flag = True

    #
    # Device register functions (8 bit)
    #

    def _read_reg(self, reg, size=1):
        """Read a register, or set of registers, to a list"""
        buf = self.bus.readfrom_mem(self.address, reg, size)
        if size == 1:
            return int(buf[0])
        return buf

    def _read_reg_into(self, reg, buf):
        """Read register(s) into a bytearray"""
        self.bus.readfrom_mem_into(self.address, reg, buf)

    def _write_reg(self, reg, val):
        """Write a single integer byte, or a bytearray, to register(s)"""
        if isinstance(val, int):
            val = bytes([val])
        self.bus.writeto_mem(self.address, reg, val)
        sleep_us(500 if self.powersave else 2)

    def _write_burst(self, data, chunk=16):
        """Burst write config (bytearray) in 16b chunks, then the remainder"""
        self._write_reg(_INIT_ADDR_0, 0)
        self._write_reg(_INIT_ADDR_1, 0)
        for i in range(len(data) // chunk):
            offs = i * chunk
            self._write_reg(_INIT_DATA, data[offs : offs + chunk])
            init_addr = ((i + 1) * chunk) // 2
            self._write_reg(_INIT_ADDR_0, (init_addr & 0x0F))
            self._write_reg(_INIT_ADDR_1, (init_addr >> 4) & 0xFF)
        remainder = len(data) % chunk
        if remainder != 0:
            offs = (len(data) // chunk) * chunk
            self._write_reg(_INIT_DATA, data[offs : offs + remainder])

    def _poll_reg(self, reg, mask, retry=10, delay=100):
        """Wait for a register bit to become true"""
        for i in range(retry):
            if self._read_reg(reg) & mask:
                return True
            sleep_ms(delay)
        return False

    def _set_bit(self, state, register, bit):
        """Set a single bit's state in a device register"""
        old = self._read_reg(register)
        new = ((~(2**bit) & 0xFF) & old) + (state << bit)
        self._write_reg(register, bytes([new]))

    #
    # Base Functions for all configs
    #

    def sensor_settings(self, gyro_odr=None, gyro_scale=None, accel_odr=None, accel_scale=None):
        """
        Set sensor Output Data Rares (ODR) and Scale
        - see init() for values
        """
        if gyro_odr is not None:
            if gyro_odr not in self.ODR:
                raise ValueError("Invalid gyro sampling rate: %d" % gyro_odr)
            self.gyro_odr = gyro_odr
        if gyro_scale is not None:
            if gyro_scale not in self.GYRO_SCALE:
                raise ValueError("Invalid gyro scaling: %d" % gyro_scale)
            self.gyro_scale = gyro_scale
        if accel_odr is not None:
            if accel_odr not in self.ODR:
                raise ValueError("Invalid accelerometer sampling rate: %d" % accel_odr)
            self.accel_odr = accel_odr
        if accel_scale is not None:
            if accel_scale not in self.ACCEL_SCALE:
                raise ValueError("Invalid accelerometer scaling: %d" % accel_scale)
            self.accel_scale = accel_scale
        # Set gyroscope scale and range.
        self._write_reg(_GYR_RANGE, self.GYRO_SCALE.index(self.gyro_scale))
        # gyr_filter_perf | gyr_bwp normal mode | ODR
        self._write_reg(_GYR_CONF, 0xA | (self.ODR.index(self.gyro_odr) + 1))
        # Set accelerometer scale and range.
        self._write_reg(_ACC_RANGE, self.ACCEL_SCALE.index(self.accel_scale))
        # acc_filter_perf | acc_bwp normal mode | ODR
        self._write_reg(_ACC_CONF, 0xA | (self.ODR.index(self.accel_odr) + 1))
        # scale factors
        self.accel_scale_factor = 32768 / self.accel_scale
        self.gyro_scale_factor = 32768 / self.gyro_scale

    def power(
        self,
        powersave=None,
        accel=None,
        gyro=None,
        acc_filter=None,
        gyr_filter=None,
        gyr_noise=None,
    ):
        """
        Set power modes;
        - See base datasheet section 4.5 'Power Modes' (page 26)
        - disabling the gyroscope produces greatest savings
          - gesture detection features do not use the gyroscope

        powersave = device 'advanced power save' mode, default False
        accel = enable/disable accellerometer, default True
        gyro = enable/disable gyroscope, default True
        acc_filter = powresave mode for accel filter, default True
        gyr_filter = powresave mode for gyro filter, default True
        gyr_noise = powersave mode for gyro noise filter, default False
        """
        if powersave in (True, False):
            self._set_bit(powersave, _PWR_CONF, 0)
            self.powersave = powersave
        if gyro in (True, False):
            self._set_bit(gyro, _PWR_CTRL, 1)
        if accel in (True, False):
            self._set_bit(accel, _PWR_CTRL, 2)
        if acc_filter in (True, False):
            self._set_bit(acc_filter, _ACC_CONF, 7)
        if gyr_filter in (True, False):
            self._set_bit(gyr_filter, _GYR_CONF, 7)
        if gyr_noise in (True, False):
            self._set_bit(gyr_noise, _GYR_CONF, 6)

    def gyro(self):
        """Returns gyroscope vector in degrees/sec."""
        f = self.gyro_scale_factor
        self._read_reg_into(_DATA_14, self._scratch)
        return (self._scratch[0] / f, self._scratch[1] / f, self._scratch[2] / f)

    def accel(self):
        """Returns acceleration vector in gravity units (9.81m/s^2)."""
        f = self.accel_scale_factor
        self._read_reg_into(_DATA_8, self._scratch)
        return (self._scratch[0] / f, self._scratch[1] / f, self._scratch[2] / f)

    def magnet(self):
        """Returns magnetometer vector if a magnetomter attached and supplied."""
        if self.bmm_magnet is not None:
            return self.bmm_magnet.magnet()
        return (0.0, 0.0, 0.0)

    def temperature(self):
        """Returns temperature value in degrees C."""
        self._read_reg_into(_TEMP_REG, self._word)
        return (self._word[0] / 512) + 23.0
