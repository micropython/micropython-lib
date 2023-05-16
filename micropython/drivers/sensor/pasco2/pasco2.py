# Infineon XENSIV PAS CO2 sensor driver for MicroPython

from machine import I2C
from utime import sleep, sleep_ms

# Sensor Register Address Stack
_PASCO2_REG_SENS_STS = const(0x01)  # Sensor status register address
_PASCO2_REG_MEAS_RATE_H = const(0x02)  # Measurement period MSB configuration register address
_PASCO2_REG_MEAS_CFG = const(0x04)  # Measurement mode configuration register address
_PASCO2_REG_CO2PPM_H = const(0x05)  # CO2 concentration result MSB register address
_PASCO2_REG_MEAS_STS = const(0x07)  # Measurement status register address
_PASCO2_REG_SENS_RST = const(0x10)  # Soft reset register address
_PASCO2_REG_PROD_ID = const(0x00)  # Product and revision ID register address

# Error codes
_PASCO2_SUCCESS = 0
_PASCO2_ERROR = -1

addr = 0
mask = 1


class PASCO2:
    """IFX - XENSIV PAS CO2 sensor driver"""

    # RegAddr, Mask, <Later extend with register access type, bit position etc.>
    regMap = {
        "REG_SENS_STS_BITF_SENS_RDY": [_PASCO2_REG_SENS_STS, 0x80],  # Sensor status bit
        "REG_MEAS_CFG_BITF_OP_MODE": [_PASCO2_REG_MEAS_CFG, 0x03],  # Operation Mode type bit
        "REG_MEAS_STS_BITF_DATA_RDY": [_PASCO2_REG_MEAS_STS, 0x10],  # Data ready status bit
        "REG_CO2PPM_H_BITF_CO2_PPM_H": [_PASCO2_REG_CO2PPM_H, 0xFF],  # Stored CO2 value bit
        "REG_PROD_ID_BITF_PROD": [_PASCO2_REG_PROD_ID, 0xE0],  # Product id bit
        "REG_PROD_ID_BITF_REV": [_PASCO2_REG_PROD_ID, 0x1F],  # Revision id bit
    }

    def __init__(self, bus, measInterval=10, sensorAddr=0x28):
        """ " Intialize the sensor and required dependencies"""
        self.bus = bus
        self.sensorAddr = sensorAddr
        self.measInterval = measInterval
        self.softResetCode = b"\xa3"

    def _read_reg(self, regAddr, bytesToRead=1):
        """Internal function to read data from the sensor register and returns it raw"""
        readVal = self.bus.readfrom_mem(self.sensorAddr, regAddr, bytesToRead)
        return readVal

    def _write_reg(self, regAddr, writeData):
        """Internal function to write data to sensor register"""
        self.bus.writeto_mem(self.sensorAddr, regAddr, writeData)

    def _is_sensor_ready(self):
        """Helper function to check the sensor status"""
        reg = self.regMap["REG_SENS_STS_BITF_SENS_RDY"]
        return self._read_reg(reg[addr])[0] & reg[mask]

    def _soft_reset(self):
        """Helper function to perform soft reset of the sensor"""
        self._write_reg(_PASCO2_REG_SENS_RST, self.softResetCode)

    def _set_mode(self, mode):
        """Helper function to set the mode of sensor. Currently supported modes:
        1. Idle
        2. Continuous
        """
        if mode == "idle":
            modeVal = 0x00
        if mode == "continuous":
            modeVal = 0x02

        reg = self.regMap["REG_MEAS_CFG_BITF_OP_MODE"]
        readData = self._read_reg(reg[addr])[0]
        writeData = bytes([(readData & ~(reg[mask])) | modeVal])
        self._write_reg(_PASCO2_REG_MEAS_CFG, writeData)

    # def _get_bit_field(self, bitField, bitValue):

    def initialize(self):
        """Public function to initialize the sensor"""
        try:
            # wait for sensor to be ready
            sensor_ready = self._is_sensor_ready()
            while not sensor_ready:
                sleep(1)
                sensor_ready = self._is_sensor_ready()

            # soft reset sensor register
            self._soft_reset()
            sleep_ms(800)

            # set measure rate
            buf = bytes([(self.measInterval >> 8) & 0xFF, self.measInterval & 0xFF])
            self._write_reg(_PASCO2_REG_MEAS_RATE_H, buf)

            # reset operation mode to idle mode
            self._set_mode("idle")

            # start continuous mode
            self._set_mode("continuous")

            return _PASCO2_SUCCESS

        except:
            return _PASCO2_ERROR

    def get_co2_value(self):
        """Public function to get the CO2 value"""
        while True:
            try:
                # get meas status
                reg = self.regMap["REG_MEAS_STS_BITF_DATA_RDY"]
                readStatus = self._read_reg(reg[addr])
                data_ready = readStatus[0] & reg[mask]

                if data_ready:
                    # get CO2 value
                    reg = self.regMap["REG_CO2PPM_H_BITF_CO2_PPM_H"]
                    readVal = self._read_reg(reg[addr], 2)
                    co2_value = (readVal[0] << 8) | readVal[1]
                    return co2_value
            except:
                return _PASCO2_ERROR

    def get_prod_id(self):
        """Public function to get the sensor product id"""
        try:
            reg = self.regMap["REG_PROD_ID_BITF_PROD"]
            readID = (self._read_reg(reg[addr])[0] & 0xE0) >> 5
            return readID

        except:
            return _PASCO2_ERROR

    def get_rev_id(self):
        """Public function to get the sensor revision id"""
        try:
            reg = self.regMap["REG_PROD_ID_BITF_REV"]
            readID = (self._read_reg(reg[addr])[0] & 0x1F) >> 0
            return readID

        except:
            return _PASCO2_ERROR
