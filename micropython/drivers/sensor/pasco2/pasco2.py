from machine import I2C
from utime import sleep, sleep_ms

# Sensor Register Address Stack
#_PASCO2_REG_PROD_ID        = const(0x00) # Product and revision ID register address
_PASCO2_REG_SENS_STS       = const(0x01) # Sensor status register address  
_PASCO2_REG_MEAS_RATE_H    = const(0x02) # Measurement period MSB configuration register address  
#_PASCO2_REG_MEAS_RATE_L    = const(0x03) # Measurement period LSB register address  
_PASCO2_REG_MEAS_CFG       = const(0x04) # Measurement mode configuration register address  
_PASCO2_REG_CO2PPM_H       = const(0x05) # CO2 concentration result MSB register address  
#_PASCO2_REG_CO2PPM_L       = const(0x06) # CO2 concentration result LSB register address  
_PASCO2_REG_MEAS_STS       = const(0x07) # Measurement status register address  
#_PASCO2_REG_INT_CFG        = const(0x08) # Interrupt pin configuration register address  
#_PASCO2_REG_ALARM_TH_H     = const(0x09) # Alarm threshold MSB register address   
_PASCO2_REG_SENS_RST       = const(0x10) # Soft reset register address  
    
#Error codes
_PASCO2_SUCCESS = 0
_PASCO2_ERROR = -1

addr = 0
mask = 1

i2c = I2C(0)

class PASCO2:
    """IFX - XENSIV PAS CO2 sensor driver"""
    regMap = { # RegAddr, Mask
    'REG_SENS_STS_BITF_SENS_RDY' : [_PASCO2_REG_SENS_STS, 0x80],
    'REG_MEAS_CFG_BITF_OP_MODE'  : [_PASCO2_REG_MEAS_CFG, 0x03],
    'REG_MEAS_STS_BITF_DATA_RDY' : [_PASCO2_REG_MEAS_STS, 0x10], # Data ready status bit
    'REG_CO2PPM_H_BITF_CO2_PPM_H': [_PASCO2_REG_CO2PPM_H, 0xFF],
    }
    
    def __init__(self, bus, measInterval=10, sensorAddr=0x28):
        self.bus = bus
        self.sensorAddr = sensorAddr
        self.measInterval = measInterval
        self.softResetCode = b"\xa3"
        
    def _read_reg(self, regAddr, bytesToRead=1):
        readVal = self.bus.readfrom_mem(self.sensorAddr, regAddr, bytesToRead)
        return readVal
    
    def _write_reg(self, regAddr, writeData):
        self.bus.writeto_mem(self.sensorAddr, regAddr, writeData)
    
    def _is_sensor_ready(self):
        reg = self.regMap['REG_SENS_STS_BITF_SENS_RDY']
        return (self._read_reg(reg[addr])[0] & reg[mask])
    
    def _soft_reset(self):
        self._write_reg(_PASCO2_REG_SENS_RST, self.softResetCode)
        
    def _set_mode(self, mode):
        if mode == 'idle': modeVal = 0x00
        if mode == 'continuous': modeVal = 0x02
        
        reg = self.regMap['REG_MEAS_CFG_BITF_OP_MODE']
        readData = self._read_reg(reg[addr])[0]
        writeData = bytes([(readData & ~(reg[mask])) | modeVal])
        self._write_reg(_PASCO2_REG_MEAS_CFG,writeData)
        
        
    def initialize(self):
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
            self._set_mode('idle')
    
            # start continuous mode
            self._set_mode('continuous')   
    
            return _PASCO2_SUCCESS

        except:
            return _PASCO2_ERROR
    
    def getCO2Value(self):
        while True:
            try: 
                # get meas status
                reg = self.regMap['REG_MEAS_STS_BITF_DATA_RDY']
                readStatus = self._read_reg(reg[addr])
                data_ready = readStatus[0] & reg[mask]

                if data_ready:    
                    # get CO2 value
                    reg = self.regMap['REG_CO2PPM_H_BITF_CO2_PPM_H']
                    readVal = self._read_reg(reg[addr], 2)
                    co2_value = (readVal[0] << 8) | readVal[1]
                    return co2_value
            except:
                return _PASCO2_ERROR