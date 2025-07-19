# MicroPython LoRa SX127x driver
# MIT license; Copyright (c) 2023 Angus Gratton
#
# LoRa is a registered trademark or service mark of Semtech Corporation or its affiliates.
#
# In comments, abbreviation "DS" = Semtech SX1276/77/78/79 Datasheet rev 7 (May 2020)
from micropython import const
from .modem import BaseModem, ConfigError, RxPacket, _clamp, _flag
from machine import Pin
import struct
import time

# Set _DEBUG to const(True) to print all register reads and writes, and current register values
# even when an update isn't needed. Plus a few additional pieces of information.
_DEBUG = const(False)

_WRITE_REG_BIT = const(1 << 7)

# Registers and fields as bytecode-zerocost constants
#
# Where possible names are direct from DS section 4.4
# (This means some names are slightly inconsistent, as per datasheet...)

_REG_FIFO = const(0x00)

_REG_OPMODE = const(0x01)

_OPMODE_LONGRANGEMODE_LORA = const(1 << 7)
_OPMODE_LONGRANGEMODE_FSK_OOK = const(0)
_OPMODE_MODE_MASK = const(0x7)
_OPMODE_MODE_SLEEP = const(0x0)
_OPMODE_MODE_STDBY = const(0x1)
_OPMODE_MODE_FSTX = const(0x2)  # Frequency synthesis (TX)
_OPMODE_MODE_TX = const(0x3)
_OPMODE_MODE_FSRX = const(0x4)  # Frequency synthesis (RX)
_OPMODE_MODE_RX_CONTINUOUS = const(0x5)
_OPMODE_MODE_RX_SINGLE = const(0x6)
_OPMODE_MODE_CAD = const(0x7)  # Channel Activity Detection

_REG_FR_MSB = const(0x06)
_REG_FR_MID = const(0x07)
_REG_FR_LSB = const(0x08)

_REG_PA_CONFIG = const(0x09)

_PA_CONFIG_PASELECT_PA_BOOST_PIN = const(1 << 7)
_PA_CONFIG_PASELECT_RFO_PIN = const(0x0)
_PA_CONFIG_MAXPOWER_SHIFT = const(0x4)
_PA_CONFIG_MAXPOWER_MASK = const(0x7)
_PA_CONFIG_OUTPUTPOWER_SHIFT = const(0)
_PA_CONFIG_OUTPUTPOWER_MASK = const(0xF)

_REG_PA_RAMP = const(0x0A)
_PA_RAMP_MASK = const(0x0F)

_REG_LNA = const(0x0C)

_LNA_GAIN_MASK = const(0x7)
_LNA_GAIN_SHIFT = const(5)

_LNA_BOOST_HF_MASK = 0x3
_LNA_BOOST_HF_SHIFT = 0x0

_REG_FIFO_ADDR_PTR = const(0x0D)
_REG_FIFO_TX_BASE_ADDR = const(0x0E)
_REG_FIFO_RX_BASE_ADDR = const(0x0F)
_REG_FIFO_RX_CURRENT_ADDR = const(0x10)

_REG_IRQ_FLAGS_MASK = const(0x11)
_REG_IRQ_FLAGS = const(0x12)

# IRQ mask bits are the same as the IRQ flag bits
_IRQ_RX_TIMEOUT = const(1 << 7)
_IRQ_RX_DONE = const(1 << 6)
_IRQ_PAYLOAD_CRC_ERROR = const(1 << 5)
_IRQ_VALID_HEADER = const(1 << 4)
_IRQ_TX_DONE = const(1 << 3)
_IRQ_CAD_DONE = const(1 << 2)
_IRQ_FHSS_CHANGE_CHANNEL = const(1 << 1)
_IRQ_CAD_DETECTED = const(1 << 0)

_REG_RX_NB_BYTES = const(0x13)
_REG_RX_HEADER_CNT_VALUE_MSB = const(0x14)
_REG_RX_HEADER_CNT_VALUE_LSB = const(0x13)
_REG_RX_PACKET_CNT_VALUE_MSB = const(0x16)
_REG_RX_PACKET_CNT_VALUE_LSB = const(0x17)

_REG_MODEM_STAT = const(0x18)
_MODEM_STAT_RX_CODING_RATE_MASK = const(0xE)
_MODEM_STAT_RX_CODING_RATE_SHIFT = const(5)
_MODEM_STAT_MODEM_CLEAR = const(1 << 4)
_MODEM_STAT_HEADER_INFO_VALID = const(1 << 3)
_MODEM_STAT_RX_ONGOING = const(1 << 2)
_MODEM_STAT_SIGNAL_SYNC = const(1 << 1)  # Signal synchronized
_MODEM_STAT_SIGNAL_DET = const(1 << 0)  # Signal detected

_REG_PKT_SNR_VAL = const(0x19)
_REG_PKT_RSSI_VAL = const(0x1A)
_REG_RSSI_VAL = const(0x1B)

_REG_HOP_CHANNEL = const(0x1C)
_HOP_CHANNEL_PLL_TIMEOUT = const(1 << 7)
_HOP_CHANNEL_CRC_ON_PAYLOAD = const(1 << 6)
_HOP_CHANNEL_FHSS_PRESENT_CHANNEL_MASK = const(0x1F)

_REG_MODEM_CONFIG1 = const(0x1D)
_MODEM_CONFIG1_BW_MASK = const(0xF)
_MODEM_CONFIG1_BW_SHIFT = const(4)
_MODEM_CONFIG1_BW7_8 = const(0x0)
_MODEM_CONFIG1_BW10_4 = const(0x1)
_MODEM_CONFIG1_BW15_6 = const(0x2)
_MODEM_CONFIG1_BW20_8 = const(0x3)
_MODEM_CONFIG1_BW31_25 = const(0x4)
_MODEM_CONFIG1_BW41_7 = const(0x5)
_MODEM_CONFIG1_BW62_5 = const(0x6)
_MODEM_CONFIG1_BW125 = const(0x7)
_MODEM_CONFIG1_BW250 = const(0x8)  # not supported in lower band (169MHz)
_MODEM_CONFIG1_BW500 = const(0x9)  # not supported in lower band (169MHz)
_MODEM_CONFIG1_CODING_RATE_MASK = const(0x7)
_MODEM_CONFIG1_CODING_RATE_SHIFT = const(1)
_MODEM_CONFIG1_CODING_RATE_45 = const(0b001)
_MODEM_CONFIG1_CODING_RATE_46 = const(0b010)
_MODEM_CONFIG1_CODING_RATE_47 = const(0b011)
_MODEM_CONFIG1_CODING_RATE_48 = const(0b100)
_MODEM_CONFIG1_IMPLICIT_HEADER_MODE_ON = const(1 << 0)

_REG_MODEM_CONFIG2 = const(0x1E)
_MODEM_CONFIG2_SF_MASK = const(0xF)  # Spreading Factor
_MODEM_CONFIG2_SF_SHIFT = const(4)
# SF values are integers 6-12 for SF6-SF12, so skipping constants for these
_MODEM_CONFIG2_SF_MIN = const(6)  # inclusive
_MODEM_CONFIG2_SF_MAX = const(12)  # inclusive

_MODEM_CONFIG2_TX_CONTINUOUS = const(1 << 3)
_MODEM_CONFIG2_RX_PAYLOAD_CRC_ON = const(1 << 2)
_MODEM_CONFIG2_SYMB_TIMEOUT_MSB_MASK = 0x3

_REG_SYMB_TIMEOUT_LSB = const(0x1F)

_REG_PREAMBLE_LEN_MSB = const(0x20)
_REG_PREAMBLE_LEN_LSB = const(0x21)

_REG_PAYLOAD_LEN = const(0x22)  # Only for implicit header mode & TX
_REG_MAX_PAYLOAD_LEN = const(0x23)

_REG_HOP_PERIOD = const(0x24)

_REG_FIFO_TXBYTE_ADDR = const(0x25)

_REG_MODEM_CONFIG3 = const(0x26)
_MODEM_CONFIG3_AGC_ON = const(1 << 2)
_MODEM_CONFIG3_LOW_DATA_RATE_OPTIMIZE = const(1 << 3)

_REG_DETECT_OPTIMIZE = const(0x31)
_DETECT_OPTIMIZE_AUTOMATIC_IF_ON = const(
    1 << 7
)  # Bit should be cleared after reset, as per errata
_DETECT_OPTIMIZE_MASK = 0x7
_DETECT_OPTIMIZE_SF6 = const(0x05)
_DETECT_OPTIMIZE_OTHER = const(0x03)

# RegInvertIQ is not correctly documented in DS Rev 7 (May 2020).
#
# The correct behaviour for interoperability with other LoRa devices is as
# written here:
# https://github.com/eclipse/upm/blob/master/src/sx1276/sx1276.cxx#L1310
#
# Same as used in the Semtech mbed driver, here:
# https://github.com/ARMmbed/mbed-semtech-lora-rf-drivers/blob/master/SX1276/SX1276_LoRaRadio.cpp#L778
# https://github.com/ARMmbed/mbed-semtech-lora-rf-drivers/blob/master/SX1276/registers/sx1276Regs-LoRa.h#L443
#
# Specifically:
# - The TX bit in _REG_INVERT_IQ is opposite to what's documented in the datasheet
#   (0x01 normal, 0x00 inverted)
# - The RX bit in _REG_INVERT_IQ is as documented in the datasheet (0x00 normal, 0x40 inverted)
# - When enabling LoRa mode, the default register value becomes 0x27 (normal RX & TX)
#   rather than the documented power-on value of 0x26.
_REG_INVERT_IQ = const(0x33)
_INVERT_IQ_RX = const(1 << 6)
_INVERT_IQ_TX_OFF = const(1 << 0)

_REG_DETECTION_THRESHOLD = const(0x37)
_DETECTION_THRESHOLD_SF6 = const(0x0C)
_DETECTION_THRESHOLD_OTHER = const(0x0A)  # SF7 to SF12

_REG_SYNC_WORD = const(0x39)

_REG_FSKOOK_IMAGE_CAL = const(0x3B)  # NOTE: Only accessible in FSK/OOK mode
_IMAGE_CAL_START = const(1 << 6)
_IMAGE_CAL_RUNNING = const(1 << 5)
_IMAGE_CAL_AUTO = const(1 << 7)

_REG_INVERT_IQ2 = const(0x3B)
_INVERT_IQ2_ON = const(0x19)
_INVERT_IQ2_OFF = const(0x1D)

_REG_DIO_MAPPING1 = const(0x40)
_DIO0_MAPPING_MASK = const(0x3)
_DIO0_MAPPING_SHIFT = const(6)
_DIO1_MAPPING_MASK = const(0x3)
_DIO1_MAPPING_SHIFT = const(4)
_DIO2_MAPPING_MASK = const(0x3)
_DIO2_MAPPING_SHIFT = const(2)
_DIO3_MAPPING_MASK = const(0x3)
_DIO3_MAPPING_SHIFT = const(0)

_REG_DIO_MAPPING2 = const(0x41)
_DIO4_MAPPING_MASK = const(0x3)
_DIO4_MAPPING_SHIFT = const(6)
_DIO5_MAPPING_MASK = const(0x3)
_DIO5_MAPPING_SHIFT = const(4)

_REG_PA_DAC = const(0x4D)
_PA_DAC_DEFAULT_VALUE = const(0x84)  # DS 3.4.3 High Power +20 dBm Operation
_PA_DAC_HIGH_POWER_20DBM = const(0x87)

_REG_VERSION = const(0x42)

# IRQs the driver masks in when receiving
_IRQ_DRIVER_RX_MASK = const(
    _IRQ_RX_DONE | _IRQ_RX_TIMEOUT | _IRQ_VALID_HEADER | _IRQ_PAYLOAD_CRC_ERROR
)


class _SX127x(BaseModem):
    # Don't instantiate this class directly, instantiate either lora.SX1276,
    #  lora.SX1277, lora.SX1278, lora.SX1279, or lora.AsyncSX1276,
    #  lora.AsyncSX1277, lora.AsyncSX1278, lora.AsyncSX1279 as applicable.

    # common IRQ masks used by the base class functions
    _IRQ_RX_COMPLETE = _IRQ_RX_DONE | _IRQ_RX_TIMEOUT
    _IRQ_TX_COMPLETE = _IRQ_TX_DONE

    def __init__(self, spi, cs, dio0=None, dio1=None, reset=None, lora_cfg=None, ant_sw=None):
        super().__init__(ant_sw)

        self._buf1 = bytearray(1)  # shared small buffers
        self._buf2 = bytearray(2)
        self._spi = spi
        self._cs = cs

        self._dio0 = dio0
        self._dio1 = dio1

        cs.init(Pin.OUT, value=1)

        if dio0:
            dio0.init(Pin.IN)
            dio0.irq(self._radio_isr, trigger=Pin.IRQ_RISING)
            if dio1:
                dio1.init(Pin.IN)
                dio1.irq(self._radio_isr, trigger=Pin.IRQ_RISING)

        # Configuration settings that need to be tracked by the driver
        # Note: a number of these are set in the base class constructor
        self._pa_boost = False

        if reset:
            # If the user supplies a reset pin argument, reset the radio
            reset.init(Pin.OUT, value=0)
            time.sleep_ms(1)
            reset(1)
            time.sleep_ms(5)

        version = self._reg_read(_REG_VERSION)
        if version != 0x12:
            raise RuntimeError("Unexpected silicon version {}".format(version))

        # wake the radio and enable LoRa mode if it's not already set
        self._set_mode(_OPMODE_MODE_STDBY)

        if lora_cfg:
            self.configure(lora_cfg)

    def configure(self, lora_cfg):
        if self._rx is not False:
            raise RuntimeError("Receiving")

        # Set frequency
        if "freq_khz" in lora_cfg:
            # Assuming F(XOSC)=32MHz (datasheet both implies this value can be different, and
            # specifies it shouldn't be different!)
            self._rf_freq_hz = int(lora_cfg["freq_khz"] * 1000)
            fr_val = self._rf_freq_hz * 16384 // 1000_000
            buf = bytes([fr_val >> 16, (fr_val >> 8) & 0xFF, fr_val & 0xFF])
            self._reg_write(_REG_FR_MSB, buf)

        # Turn on/off automatic image re-calibration if temperature changes. May lead to dropped
        # packets if enabled.
        if "auto_image_cal" in lora_cfg:
            self._set_mode(_OPMODE_MODE_STDBY, False)  # Disable LoRa mode to access FSK/OOK
            self._reg_update(
                _REG_FSKOOK_IMAGE_CAL,
                _IMAGE_CAL_AUTO,
                _flag(_IMAGE_CAL_AUTO, lora_cfg["auto_image_cal"]),
            )
            self._set_mode(_OPMODE_MODE_STDBY)  # Switch back to LoRa mode

        # Note: Common pattern below is to generate a new register value and an update_mask,
        # and then call self._reg_update(). self._reg_update() is a
        # no-op if update_mask==0 (no bits to change).

        # Update _REG_PA_CONFIG
        pa_config = 0x0
        update_mask = 0x0

        # Ref DS 3.4.2 "RF Power Amplifiers"
        if "tx_ant" in lora_cfg:
            self._pa_boost = lora_cfg["tx_ant"].upper() == "PA_BOOST"
            pa_boost_bit = (
                _PA_CONFIG_PASELECT_PA_BOOST_PIN if self._pa_boost else _PA_CONFIG_PASELECT_RFO_PIN
            )
            pa_config |= pa_boost_bit
            update_mask |= pa_boost_bit
            if not self._pa_boost:
                # When using RFO, _REG_PA_DAC can keep default value always
                # (otherwise, it's set when output_power is set in next block)
                self._reg_write(_REG_PA_DAC, _PA_DAC_DEFAULT_VALUE)

        if "output_power" in lora_cfg:
            # See DS 3.4.2 RF Power Amplifiers
            dbm = int(lora_cfg["output_power"])
            if self._pa_boost:
                if dbm >= 20:
                    output_power = 0x15  # 17dBm setting
                    pa_dac = _PA_DAC_HIGH_POWER_20DBM
                else:
                    dbm = _clamp(dbm, 2, 17)  # +2 to +17dBm only
                    output_power = dbm - 2
                    pa_dac = _PA_DAC_DEFAULT_VALUE
                self._reg_write(_REG_PA_DAC, pa_dac)
            else:
                # In RFO mode, Output Power is computed from two register fields
                # - MaxPower and OutputPower.
                #
                # Do what the Semtech LoraMac-node driver does here, which is to
                # set max_power at one extreme or the other (0 or 7) and then
                # calculate the output_power setting based on this baseline.
                dbm = _clamp(dbm, -4, 15)
                if dbm > 0:
                    # MaxPower to maximum
                    pa_config |= _PA_CONFIG_MAXPOWER_MASK << _PA_CONFIG_MAXPOWER_SHIFT

                    # Pout (dBm) == 10.8dBm + 0.6*maxPower - (15 - register value)
                    # 10.8+0.6*7 == 15dBm, so pOut = register_value (0 to 15 dBm)
                    output_power = dbm
                else:
                    # MaxPower field will be set to 0

                    # Pout (dBm) == 10.8dBm - (15 - OutputPower)
                    # OutputPower == Pout (dBm) + 4.2
                    output_power = dbm + 4  # round down to 4.0, to keep using integer math

            pa_config |= output_power << _PA_CONFIG_OUTPUTPOWER_SHIFT
            update_mask |= (
                _PA_CONFIG_OUTPUTPOWER_MASK << _PA_CONFIG_OUTPUTPOWER_SHIFT
                | _PA_CONFIG_MAXPOWER_MASK << _PA_CONFIG_MAXPOWER_SHIFT
            )

        self._reg_update(_REG_PA_CONFIG, update_mask, pa_config)

        if "pa_ramp_us" in lora_cfg:
            # other fields in this register are reserved to 0 or unused
            self._reg_write(
                _REG_PA_RAMP,
                self._get_pa_ramp_val(
                    lora_cfg,
                    [10, 12, 15, 20, 25, 31, 40, 50, 62, 100, 125, 250, 500, 1000, 2000, 3400],
                ),
            )

        # If a hard reset happened then flags should be cleared already and mask should
        # default to fully enabled, but let's be "belts and braces" sure
        self._reg_write(_REG_IRQ_FLAGS, 0xFF)
        self._reg_write(_REG_IRQ_FLAGS_MASK, 0)  # do IRQ masking in software for now

        # Update MODEM_CONFIG1
        modem_config1 = 0x0
        update_mask = 0x0
        if "bw" in lora_cfg:
            bw = str(lora_cfg["bw"])
            bw_reg_val, self._bw_hz = {
                "7.8": (_MODEM_CONFIG1_BW7_8, 7800),
                "10.4": (_MODEM_CONFIG1_BW10_4, 10400),
                "15.6": (_MODEM_CONFIG1_BW15_6, 15600),
                "20.8": (_MODEM_CONFIG1_BW20_8, 20800),
                "31.25": (_MODEM_CONFIG1_BW31_25, 31250),
                "41.7": (_MODEM_CONFIG1_BW41_7, 41700),
                "62.5": (_MODEM_CONFIG1_BW62_5, 62500),
                "125": (_MODEM_CONFIG1_BW125, 125000),
                "250": (_MODEM_CONFIG1_BW250, 250000),
                "500": (_MODEM_CONFIG1_BW500, 500000),
            }[bw]
            modem_config1 |= bw_reg_val << _MODEM_CONFIG1_BW_SHIFT
            update_mask |= _MODEM_CONFIG1_BW_MASK << _MODEM_CONFIG1_BW_SHIFT

        if "freq_khz" in lora_cfg or "bw" in lora_cfg:
            # Workaround for Errata Note 2.1 "Sensitivity Optimization with a 500 kHz bandwidth"
            if self._bw_hz == 500000 and 862_000_000 <= self._rf_freq_hz <= 1020_000_000:
                self._reg_write(0x36, 0x02)
                self._reg_write(0x3A, 0x64)
            elif self._bw_hz == 500000 and 410_000_000 <= self._rf_freq_hz <= 525_000_000:
                self._reg_write(0x36, 0x02)
                self._reg_write(0x3A, 0x7F)
            else:
                # "For all other combinations of bandiwdth/frequencies, register at address 0x36
                # should be re-set to value 0x03 and the value at address 0x3a will be
                # automatically selected by the chip"
                self._reg_write(0x36, 0x03)

        if "coding_rate" in lora_cfg:
            self._coding_rate = int(lora_cfg["coding_rate"])
            if self._coding_rate < 5 or self._coding_rate > 8:
                raise ConfigError("coding_rate")
            # _MODEM_CONFIG1_CODING_RATE_45 == value 5 == 1
            modem_config1 |= (self._coding_rate - 4) << _MODEM_CONFIG1_CODING_RATE_SHIFT
            update_mask |= _MODEM_CONFIG1_CODING_RATE_MASK << _MODEM_CONFIG1_CODING_RATE_SHIFT

        if "implicit_header" in lora_cfg:
            self._implicit_header = lora_cfg["implicit_header"]
            modem_config1 |= _flag(_MODEM_CONFIG1_IMPLICIT_HEADER_MODE_ON, self._implicit_header)
            update_mask |= _MODEM_CONFIG1_IMPLICIT_HEADER_MODE_ON

        self._reg_update(_REG_MODEM_CONFIG1, update_mask, modem_config1)

        # Update MODEM_CONFIG2, for any fields that changed
        modem_config2 = 0
        update_mask = 0
        if "sf" in lora_cfg:
            sf = self._sf = int(lora_cfg["sf"])

            if sf < _MODEM_CONFIG2_SF_MIN or sf > _MODEM_CONFIG2_SF_MAX:
                raise ConfigError("sf")
            if sf == 6 and not self._implicit_header:
                # DS 4.1.12 "Spreading Factor"
                raise ConfigError("SF6 requires implicit_header mode")

            # Update these registers when writing 'SF'
            self._reg_write(
                _REG_DETECTION_THRESHOLD,
                _DETECTION_THRESHOLD_SF6 if sf == 6 else _DETECTION_THRESHOLD_OTHER,
            )
            # This field has a reserved non-zero field, so do a read-modify-write update
            self._reg_update(
                _REG_DETECT_OPTIMIZE,
                _DETECT_OPTIMIZE_AUTOMATIC_IF_ON | _DETECT_OPTIMIZE_MASK,
                _DETECT_OPTIMIZE_SF6 if sf == 6 else _DETECT_OPTIMIZE_OTHER,
            )

            modem_config2 |= sf << _MODEM_CONFIG2_SF_SHIFT
            update_mask |= _MODEM_CONFIG2_SF_MASK << _MODEM_CONFIG2_SF_SHIFT

        if "crc_en" in lora_cfg:
            self._crc_en = lora_cfg["crc_en"]
            # I had to double-check the datasheet about this point:
            # 1. In implicit header mode, this bit is used on both RX & TX and
            #    should be set to get CRC generation on TX and/or checking on RX.
            # 2. In explicit header mode, this bit is only used on TX (should CRC
            #    be added and CRC flag set in header) and ignored on RX (CRC flag
            #    read from header instead).
            modem_config2 |= _flag(_MODEM_CONFIG2_RX_PAYLOAD_CRC_ON, self._crc_en)
            update_mask |= _MODEM_CONFIG2_RX_PAYLOAD_CRC_ON

        self._reg_update(_REG_MODEM_CONFIG2, update_mask, modem_config2)

        # Update _REG_INVERT_IQ
        #
        # See comment about this register's undocumented weirdness at top of
        # file above _REG_INVERT_IQ constant.
        #
        # Note also there is a second register invert_iq2 which may be set differently
        # for transmit vs receive, see _set_invert_iq2() for that one.
        invert_iq = 0x0
        update_mask = 0x0
        if "invert_iq_rx" in lora_cfg:
            self._invert_iq[0] = lora_cfg["invert_iq_rx"]
            invert_iq |= _flag(_INVERT_IQ_RX, lora_cfg["invert_iq_rx"])
            update_mask |= _INVERT_IQ_RX
        if "invert_iq_tx" in lora_cfg:
            self._invert_iq[1] = lora_cfg["invert_iq_tx"]
            invert_iq |= _flag(_INVERT_IQ_TX_OFF, not lora_cfg["invert_iq_tx"])  # Inverted
            update_mask |= _INVERT_IQ_TX_OFF
        self._reg_update(_REG_INVERT_IQ, update_mask, invert_iq)

        if "preamble_len" in lora_cfg:
            self._preamble_len = lora_cfg["preamble_len"]
            self._reg_write(_REG_PREAMBLE_LEN_MSB, struct.pack(">H", self._preamble_len))

        # Update MODEM_CONFIG3, for any fields that have changed
        modem_config3 = 0
        update_mask = 0

        if "sf" in lora_cfg or "bw" in lora_cfg:
            # Changing either SF or BW means the Low Data Rate Optimization may need to be changed
            #
            # note: BaseModem.get_n_symbols_x4() assumes this value is set automatically
            # as follows.
            modem_config3 |= _flag(_MODEM_CONFIG3_LOW_DATA_RATE_OPTIMIZE, self._get_ldr_en())
            update_mask |= _MODEM_CONFIG3_LOW_DATA_RATE_OPTIMIZE

        if "lna_gain" in lora_cfg:
            lna_gain = lora_cfg["lna_gain"]
            update_mask |= _MODEM_CONFIG3_AGC_ON
            if lna_gain is None:  # Setting 'None' means 'Auto'
                modem_config3 |= _MODEM_CONFIG3_AGC_ON
            else:  # numeric register value
                # Clear the _MODEM_CONFIG3_AGC_ON bit, and write the manual LNA gain level 1-6
                # to the register
                self._reg_update(
                    _REG_LNA, _LNA_GAIN_MASK << _LNA_GAIN_SHIFT, lna_gain << _LNA_GAIN_SHIFT
                )

        if "rx_boost" in lora_cfg:
            self._reg_update(
                _REG_LNA,
                _LNA_BOOST_HF_MASK << _LNA_BOOST_HF_SHIFT,
                _flag(0x3, lora_cfg["lna_boost_hf"]),
            )

        self._reg_update(_REG_MODEM_CONFIG3, update_mask, modem_config3)

        if "syncword" in lora_cfg:
            self._reg_write(_REG_SYNC_WORD, lora_cfg["syncword"])

    def _reg_write(self, reg, value):
        self._cs(0)
        if isinstance(value, int):
            self._buf2[0] = reg | _WRITE_REG_BIT
            self._buf2[1] = value
            self._spi.write(self._buf2)
            if _DEBUG:
                dbg = hex(value)
        else:  # value is a buffer
            self._buf1[0] = reg | _WRITE_REG_BIT
            self._spi.write(self._buf1)
            self._spi.write(value)
            if _DEBUG:
                dbg = value.hex()
        self._cs(1)

        if _DEBUG:
            print("W {:#x} ==> {}".format(reg, dbg))
            self._reg_read(reg)  # log the readback as well

    def _reg_update(self, reg, update_mask, new_value):
        # Update register address 'reg' with byte value new_value, as masked by
        # bit mask update_mask. Bits not set in update_mask will be kept at
        # their pre-existing values in the register.
        #
        # If update_mask is zero, this function is a no-op and returns None.
        # If update_mask is not zero, this function updates 'reg' and returns
        # the previous complete value of 'reg' as a result.
        #
        # Note: this function has no way of detecting a race condition if the
        # modem updates any bits in 'reg' that are unset in update_mask, at the
        # same time a read/modify/write is occurring. Any such changes are
        # overwritten with the original values.

        if not update_mask:  # short-circuit if nothing to change
            if _DEBUG:
                # Log the current value if DEBUG is on
                # (Note the compiler will optimize this out otherwise)
                self._reg_read(reg)
            return
        old_value = self._reg_read(reg)
        value = ((old_value & ~update_mask) & 0xFF) | (new_value & update_mask)
        if old_value != value:
            self._reg_write(reg, value)
        return old_value

    def _reg_read(self, reg):
        # Read and return a single register value at address 'reg'
        self._buf2[0] = reg
        self._buf2[1] = 0xFF
        self._cs(0)
        self._spi.write_readinto(self._buf2, self._buf2)
        self._cs(1)
        if _DEBUG:
            print("R {:#x} <== {:#x}".format(reg, self._buf2[1]))
        return self._buf2[1]

    def _reg_readinto(self, reg, buf):
        # Read and return one or more register values starting at address 'reg',
        # into buffer 'buf'.
        self._cs(0)
        self._spi.readinto(self._buf1, reg)
        self._spi.readinto(buf)
        if _DEBUG:
            print("R {:#x} <== {}".format(reg, buf.hex()))
        self._cs(1)

    def _get_mode(self):
        # Return the current 'Mode' field in RegOpMode
        return self._reg_read(_REG_OPMODE) & _OPMODE_MODE_MASK

    def _set_mode(self, mode, lora_en=True):
        # Set the 'Mode' and 'LongRangeMode' fields in RegOpMode
        # according to 'mode' and 'lora_en', respectively.
        #
        # If enabling or disabling LoRa mode, the radio is automatically
        # switched into Sleep mode as required and then the requested mode is
        # set (if not sleep mode).
        #
        # Returns the previous value of the RegOpMode register (unmasked).
        mask = _OPMODE_LONGRANGEMODE_LORA | _OPMODE_MODE_MASK
        lora_val = _flag(_OPMODE_LONGRANGEMODE_LORA, lora_en)
        old_value = self._reg_read(_REG_OPMODE)
        new_value = (old_value & ~mask) | lora_val | mode

        if lora_val != (old_value & _OPMODE_LONGRANGEMODE_LORA):
            # Need to switch into Sleep mode in order to change LongRangeMode flag
            self._reg_write(_REG_OPMODE, _OPMODE_MODE_SLEEP | lora_val)

        if new_value != old_value:
            self._reg_write(_REG_OPMODE, new_value)

            if _DEBUG:
                print(
                    "Mode {} -> {} ({:#x})".format(
                        old_value & _OPMODE_MODE_MASK, mode, self._reg_read(_REG_OPMODE)
                    )
                )

        return old_value

    def _set_invert_iq2(self, val):
        # Set the InvertIQ2 register on/off as needed, unless it is already set to the correct
        # level
        if self._invert_iq[2] == val:
            return  # already set to the level we want
        self._reg_write(_REG_INVERT_IQ2, _INVERT_IQ2_ON if val else _INVERT_IQ2_OFF)
        self._invert_iq[2] = val

    def _standby(self):
        # Send the command for standby mode.
        #
        # **Don't call this function directly, call standby() instead.**
        #
        # (This private version doesn't update the driver's internal state.)
        old_mode = self._set_mode(_OPMODE_MODE_STDBY) & _OPMODE_MODE_MASK
        if old_mode not in (_OPMODE_MODE_STDBY, _OPMODE_MODE_SLEEP):
            # If we just cancelled sending or receiving, clear any pending IRQs
            self._reg_write(_REG_IRQ_FLAGS, 0xFF)

    def sleep(self):
        # Put the modem into sleep mode. Modem will wake automatically the next
        # time host asks it for something, or call standby() to wake it manually.
        self.standby()  # save some code size, this clears driver state for us
        self._set_mode(_OPMODE_MODE_SLEEP)

    def is_idle(self):
        # Returns True if the modem is idle (either in standby or in sleep).
        #
        # Note this function can return True in the case where the modem has temporarily gone to
        # standby, but there's a receive configured in software that will resume receiving the
        # next time poll_recv() or poll_send() is called.
        return self._get_mode() in (_OPMODE_MODE_STDBY, _OPMODE_MODE_SLEEP)

    def calibrate_image(self):
        # Run the modem Image & RSSI calibration process to improve receive performance.
        #
        # calibration will be run in the HF or LF band automatically, depending on the
        # current radio configuration.
        #
        # See DS 2.1.3.8 Image and RSSI Calibration. Idea to disable TX power
        # comes from Semtech's sx1276 driver which does this.

        pa_config = self._reg_update(_REG_PA_CONFIG, 0xFF, 0)  # disable TX power

        self._set_mode(_OPMODE_MODE_STDBY, False)  # Switch to FSK/OOK mode to expose RegImageCal

        self._reg_update(_REG_FSKOOK_IMAGE_CAL, _IMAGE_CAL_START, _IMAGE_CAL_START)
        while self._reg_read(_REG_FSKOOK_IMAGE_CAL) & _IMAGE_CAL_RUNNING:
            time.sleep_ms(1)

        self._set_mode(_OPMODE_MODE_STDBY)  # restore LoRA mode

        self._reg_write(_REG_PA_CONFIG, pa_config)  # restore previous TX power

    def calibrate(self):
        # Run a full calibration.
        #
        # For SX1276, this means just the image & RSSI calibration as no other runtime
        # calibration is implemented in the modem.
        self.calibrate_image()

    def start_recv(self, timeout_ms=None, continuous=False, rx_length=0xFF):
        # Start receiving.
        #
        # Part of common low-level modem API, see README.md for usage.
        super().start_recv(timeout_ms, continuous, rx_length)  # sets self._rx

        # will_irq if DIO0 and DIO1 both hooked up, or DIO0 and no timeout
        will_irq = self._dio0 and (self._dio1 or timeout_ms is None)

        if self._tx:
            # Send is in progress and has priority, _check_recv() will start receive
            # once send finishes (caller needs to call poll_send() for this to happen.)
            if _DEBUG:
                print("Delaying receive until send completes")
            return will_irq

        # Put the modem in a known state. It's possible a different
        # receive was in progress, this prevent anything changing while
        # we set up the new receive
        self._standby()  # calling private version to keep driver state as-is

        # Update the InvertIQ2 setting for RX
        self._set_invert_iq2(self._invert_iq[0])

        if self._implicit_header:
            # Payload length only needs to be set in implicit header mode
            self._reg_write(_REG_PAYLOAD_LEN, rx_length)

        if self._dio0:
            # Field value is 0, for DIO0 = RXDone
            update_mask = _DIO0_MAPPING_MASK << _DIO0_MAPPING_SHIFT
            if self._dio1:
                # Field value also 0, for DIO1 = RXTimeout
                update_mask |= _DIO1_MAPPING_MASK << _DIO1_MAPPING_SHIFT
            self._reg_update(_REG_DIO_MAPPING1, update_mask, 0)

        if not continuous:
            # Unlike SX1262, SX1276 doesn't have a "single RX no timeout" mode. So we set the
            # maximum hardware timeout and resume RX in software if needed.
            if timeout_ms is None:
                timeout_syms = 1023
            else:
                t_sym_us = self._get_t_sym_us()
                timeout_syms = (timeout_ms * 1000 + t_sym_us - 1) // t_sym_us  # round up

                # if the timeout is too long for the modem, the host will
                # automatically resume it in software. If the timeout is too
                # short for the modem, round it silently up to the minimum
                # timeout.
                timeout_syms = _clamp(timeout_syms, 4, 1023)
            self._reg_update(
                _REG_MODEM_CONFIG2,
                _MODEM_CONFIG2_SYMB_TIMEOUT_MSB_MASK,
                timeout_syms >> 8,
            )
            self._reg_write(_REG_SYMB_TIMEOUT_LSB, timeout_syms & 0xFF)

        # Allocate the full FIFO for RX
        self._reg_write(_REG_FIFO_ADDR_PTR, 0)
        self._reg_write(_REG_FIFO_RX_BASE_ADDR, 0)

        self._set_mode(_OPMODE_MODE_RX_CONTINUOUS if continuous else _OPMODE_MODE_RX_SINGLE)

        return will_irq

    def _rx_flags_success(self, flags):
        # Returns True if IRQ flags indicate successful receive.
        # Specifically, from the bits in _IRQ_DRIVER_RX_MASK:
        # - _IRQ_RX_DONE must be set
        # - _IRQ_RX_TIMEOUT must not be set
        # - _IRQ_PAYLOAD_CRC_ERROR must not be set
        # - _IRQ_VALID_HEADER must be set if we're using explicit packet mode, ignored otherwise
        return flags & _IRQ_DRIVER_RX_MASK == _IRQ_RX_DONE | _flag(
            _IRQ_VALID_HEADER, not self._implicit_header
        )

    def _get_irq(self):
        return self._reg_read(_REG_IRQ_FLAGS)

    def _clear_irq(self, to_clear=0xFF):
        return self._reg_write(_REG_IRQ_FLAGS, to_clear)

    def _read_packet(self, rx_packet, flags):
        # Private function to read received packet (RxPacket object) from the
        # modem, if there is one.
        #
        # Called from poll_recv() function, which has already checked the IRQ flags
        # and verified a valid receive happened.

        ticks_ms = self._get_last_irq()  # IRQ timestamp for the receive

        rx_payload_len = self._reg_read(_REG_RX_NB_BYTES)

        if rx_packet is None or len(rx_packet) != rx_payload_len:
            rx_packet = RxPacket(rx_payload_len)

        self._reg_readinto(_REG_FIFO, rx_packet)

        rx_packet.ticks_ms = ticks_ms
        # units: dB*4
        rx_packet.snr = self._reg_read(_REG_PKT_SNR_VAL)
        if rx_packet.snr & 0x80:  # Signed 8-bit integer
            # (avoiding using struct here to skip a heap allocation)
            rx_packet.snr -= 0x100
        # units: dBm
        rx_packet.rssi = self._reg_read(_REG_PKT_RSSI_VAL) - (157 if self._pa_boost else 164)
        rx_packet.crc_error = flags & _IRQ_PAYLOAD_CRC_ERROR != 0
        return rx_packet

    def prepare_send(self, packet):
        # Prepare modem to start sending. Should be followed by a call to start_send()
        #
        # Part of common low-level modem API, see README.md for usage.
        if len(packet) > 255:
            raise ValueError("packet too long")

        # Put the modem in a known state. Any current receive is suspended at this point,
        # but calling _check_recv() will resume it later.
        self._standby()  # calling private version to keep driver state as-is

        if self._ant_sw:
            self._ant_sw.tx(self._pa_boost)

        self._last_irq = None

        if self._dio0:
            self._reg_update(
                _REG_DIO_MAPPING1,
                _DIO0_MAPPING_MASK << _DIO0_MAPPING_SHIFT,
                1 << _DIO0_MAPPING_SHIFT,
            )  # DIO0 = TXDone

        # Update the InvertIQ2 setting for TX
        self._set_invert_iq2(self._invert_iq[1])

        # Allocate the full FIFO for TX
        self._reg_write(_REG_FIFO_ADDR_PTR, 0)
        self._reg_write(_REG_FIFO_TX_BASE_ADDR, 0)

        self._reg_write(_REG_PAYLOAD_LEN, len(packet))

        self._reg_write(_REG_FIFO, packet)

        # clear the TX Done flag in case a previous call left it set
        # (won't happen unless poll_send() was not called)
        self._reg_write(_REG_IRQ_FLAGS, _IRQ_TX_DONE)

    def start_send(self):
        # Actually start a send that was loaded by calling prepare_send().
        #
        # This is split into a separate function to allow more precise timing.
        #
        # The driver doesn't verify the caller has done the right thing here, the
        # modem will no doubt do something weird if prepare_send() was not called!
        #
        # Part of common low-level modem API, see README.md for usage.
        self._set_mode(_OPMODE_MODE_TX)

        self._tx = True

        return self._dio0 is not None  # will_irq if dio0 is set

    def _irq_flag_tx_done(self):
        return _IRQ_TX_DONE


# Define the actual modem classes that use the SyncModem & AsyncModem "mixin-like" classes
# to create sync and async variants.

try:
    from .sync_modem import SyncModem

    class SX1276(_SX127x, SyncModem):
        pass

    # Implementation note: Currently the classes SX1276, SX1277, SX1278 and
    # SX1279 are actually all SX1276. Perhaps in the future some subclasses with
    # software enforced limits can be added to this driver, but the differences
    # appear very minor:
    #
    # - SX1276 seems like "baseline" with max freq.
    # - SX1277 supports max SF level of 9.
    # - SX1278 supports max freq 525MHz, therefore has no RFO_HF and RFI_HF pins.
    # - SX1279 supports max freq 960MHz.
    #
    # There also appears to be no difference in silicon interface or register values to determine
    # which model is connected.
    SX1277 = SX1278 = SX1279 = SX1276

except ImportError:
    pass

try:
    from .async_modem import AsyncModem

    class AsyncSX1276(_SX127x, AsyncModem):
        pass

    # See comment above about currently identical implementations
    AsyncSX1277 = AsyncSX1278 = AsyncSX1279 = AsyncSX1276

except ImportError:
    pass
