# Micropython driver for temperature/humidity sensors SHT3x/SHT4x
#
# Example usage on picoboard:
# @code{.py}
#    from machine import Pin, I2C
#    from sht import SHT
#    import time
#    i2c = I2C(0, scl=Pin(5), sda=Pin(4))
#    sensor = SHT(i2c)
#    sensor.start_measure(2)
#    while True:
#        time.sleep(0.01)
#        t_raw, t_val, h_raw, h_val, isvalid = sensor.get_measure_results()
#        if isvalid is not None:
#            break
#    print(f"{t_raw}, {t_val} °C, {h_raw}, {h_val} %RH, {isvalid}")
# @endcode
#

from machine import I2C
import time


class SHT:
    SHT3x = 0x30
    SHT4x = 0x40

    # Init SHT
    # @param i2c  I2C interface
    # @param addr I2C addr (default = 0x44)
    # @param sht  SHT type
    #             0x00 (autodetect SHT type)
    #             self.SHT3x
    #             self.SHT4x
    def __init__(self, i2c, addr=0x44, sht=0x00):
        self.i2c = i2c
        self.i2c_addr = addr
        self.sht = sht
        if self.sht == 0x00:
            self.sht = self.detect_sht_type()
        else:
            self.sht = sht

    # Verify checksum
    # @param data     data bytes
    # @param checksum received crc
    # @return crc status
    #     0 = crc does not match
    #     1 = crc ok
    def _check_crc(self, data, checksum):
        crc = 0xFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x80:
                    crc = (crc << 1) ^ 0x31
                else:
                    crc = crc << 1
        crc = crc & 0xFF
        return checksum == crc

    # Autodetect SHT type
    # @return SHT type
    #     self.SHT3x = SHT30/31/35
    #     self.SHT4x = SHT40/41/45
    #     0xFF = unknown
    def detect_sht_type(self):
        sht = 0xFF
        # try reading status of SHT3x
        try:
            self.i2c.writeto(self.i2c_addr, b"\xf3\x2d", False)
            time.sleep(0.01)
            response = self.i2c.readfrom(self.i2c_addr, 3)
            if self._check_crc(response[0:2], response[2]):
                sht = self.SHT3x
        except OSError:
            pass
        if sht == 0xFF:
            # try reading serial number of SHT4x
            try:
                self.i2c.writeto(self.i2c_addr, b"\x89", False)
                time.sleep(0.01)
                response = self.i2c.readfrom(self.i2c_addr, 6)
                if self._check_crc(response[3:5], response[5]):
                    sht = self.SHT4x
            except OSError:
                pass
        return sht

    # Start measurement
    # @param precision 0..2 [Low, Medlium, High]
    # @return None
    def start_measure(self, precision):
        if self.sht == self.SHT3x:
            p_byte = [b"\x16", b"\x0b", b"\x00"]
            self.i2c.writeto(self.i2c_addr, b"\x24" + p_byte[precision], False)
        if self.sht == self.SHT4x:
            cmd = [b"\xe0", b"\xf6", b"\xfd"]
            self.i2c.writeto(self.i2c_addr, cmd[precision], False)

    # Get the measurement values
    # @details
    #   As long as no values available all return parameter are None.
    #   If values not equal None are returned the measurement has been completed
    #   and needs to be restarted again for a new measurement.
    # @return temperature[raw], temperature[°C], humidity[raw], humidity[%RH], valid
    def get_measure_results(self):
        try:
            response = self.i2c.readfrom(self.i2c_addr, 6)
            t_bytes = response[0:2]
            t_raw = int.from_bytes(t_bytes, "big")
            t_val = (175 * t_raw) / 0xFFFF - 45
            isvalid = self._check_crc(t_bytes, response[2])
            h_bytes = response[3:5]
            h_raw = int.from_bytes(h_bytes, "big")
            h_val = (100 * h_raw) / 0xFFFF
            isvalid &= self._check_crc(h_bytes, response[5])
            return t_raw, round(t_val, 2), h_raw, round(h_val, 2), bool(isvalid)
        except OSError:
            # OSError: [Errno 5] EIO as long as measurement has not completed
            return None, None, None, None, None
