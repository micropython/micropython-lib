# MicroPython LoRa SX126x (SX1261, SX1262) driver
# MIT license; Copyright (c) 2023 Angus Gratton
#
# LoRa is a registered trademark or service mark of Semtech Corporation or its affiliates.
#
# In comments, abbreviation "DS" = Semtech SX1261/62 Datasheet Rev 2.1 (December 2021)
import struct
import time
from micropython import const
from machine import Pin
from .modem import BaseModem, ConfigError, RxPacket, _clamp, _flag

# Set _DEBUG to const(True) to print all SPI commands sent to the device, and all responses,
# plus a few additional pieces of information.
_DEBUG = const(False)

_REG_RXGAINCR = const(0x8AC)  # Reset value 0x94
_REG_LSYNCRH = const(0x740)
_REG_LSYNCRL = const(0x741)

_CMD_CFG_DIO_IRQ = const(0x08)  # args: IrqMask, Irq1Mask, Irq2Mask,. Irq3Mask
_CMD_CLR_ERRORS = const(0x07)
_CMD_CLR_IRQ_STATUS = const(0x02)  # no args
_CMD_GET_ERROR = const(0x17)
_CMD_GET_IRQ_STATUS = const(0x12)  # args: (r) Status, IrqStatus
_CMD_GET_RX_BUFFER_STATUS = const(0x13)  # args: (r) Status, RxPayloadLength, RxBufferPointer
# NOTE: _CMD_GET_STATUS seems to have an issue, see _get_status() function below.
_CMD_GET_STATUS = const(0xC0)  # args: (r) Status
_CMD_GET_PACKET_STATUS = const(0x14)
_CMD_READ_REGISTER = const(0x1D)  # args: addr (2b), status, (r) Data0 ... DataN
_CMD_READ_BUFFER = const(0x1E)  # args: Offset, (r) Status, Data0 ... DataN
_CMD_SET_BUFFER_BASE_ADDRESS = const(0x8F)  # args: TxBaseAddr, RxBaseAddr
_CMD_SET_MODULATION_PARAMS = const(0x8B)  # args (LoRa): Sf, Bw, Cr, Ldro
_CMD_SET_PACKET_PARAMS = const(
    0x8C
)  # args (LoRa): PbLength, HeaderType, PayloadLength, CrcType, InvertIQ
_CMD_SET_PACKET_TYPE = const(0x8A)  # args: PktType
_CMD_SET_PA_CONFIG = const(0x95)  # args: PaDutyCycle, HpMax, HpSel, 0x01
_CMD_SET_RF_FREQUENCY = const(0x86)  # args: RfFreg
_CMD_SET_RX = const(0x82)  # args: Timeout
_CMD_SET_SLEEP = const(0x84)  # args: SleepCfg
_CMD_SET_STANDBY = const(0x80)  # args: StandbyCfg
_CMD_SET_DIO3_AS_TCXO_CTRL = const(0x97)  # args: Trim, Timeout (3b)
_CMD_SET_DIO2_AS_RF_SWITCH_CTRL = const(0x9D)
_CMD_SET_TX = const(0x83)  # args: Timeout
_CMD_SET_TX_PARAMS = const(0x8E)  # args: Power, RampTime
_CMD_WRITE_BUFFER = const(0x0E)  # args: Offset, Data0 ... DataN
_CMD_WRITE_REGISTER = const(0x0D)  # args: Addr, Data0 ... Data N

_CMD_CALIBRATE = const(0x89)
_CMD_CALIBRATE_IMAGE = const(0x98)

_STATUS_MODE_MASK = const(0x7 << 4)
_STATUS_MODE_SHIFT = const(4)
_STATUS_MODE_STANDBY_RC = const(0x2)
_STATUS_MODE_STANDBY_HSE32 = const(0x3)
_STATUS_MODE_FS = const(0x4)
_STATUS_MODE_RX = const(0x5)
_STATUS_MODE_TX = const(0x6)

_STATUS_CMD_MASK = const(0x6)  # bits 1-3, bit 0 is reserved
_STATUS_CMD_SHIFT = const(1)
_STATUS_CMD_DATA_AVAIL = const(0x2)
_STATUS_CMD_TIMEOUT = const(0x3)
_STATUS_CMD_ERROR = const(0x4)
_STATUS_CMD_EXEC_FAIL = const(0x5)
_STATUS_CMD_TX_COMPLETE = const(0x6)

_CFG_SF_MIN = const(6)  # inclusive
_CFG_SF_MAX = const(12)  # inclusive

_IRQ_TX_DONE = const(1 << 0)
_IRQ_RX_DONE = const(1 << 1)
_IRQ_PREAMBLE_DETECTED = const(1 << 2)
_IRQ_SYNC_DETECTED = const(1 << 3)
_IRQ_HEADER_VALID = const(1 << 4)
_IRQ_HEADER_ERR = const(1 << 5)
_IRQ_CRC_ERR = const(1 << 6)
_IRQ_CAD_DONE = const(1 << 7)
_IRQ_CAD_DETECTED = const(1 << 8)
_IRQ_TIMEOUT = const(1 << 9)

# Register values
_REG_IQ_POLARITY_SETUP = const(0x0736)
_REG_RX_GAIN = const(0x08AC)
_REG_RTC_CTRL = const(0x0902)  # DS 15.3 has a typo on this value! Confirmed from Semtech driver
_REG_EVT_CLR = const(0x0944)
_REG_EVT_CLR_MASK = const(0x02)

# IRQs the driver cares about when receiving
_IRQ_DRIVER_RX_MASK = const(_IRQ_RX_DONE | _IRQ_TIMEOUT | _IRQ_CRC_ERR | _IRQ_HEADER_ERR)


# Except when entering/waking from sleep, typical busy period <105us (ref RM0453 Table 33)
#
# However, if dio3_tcxo_start_time_us is set then can take a longer
# time to become valid, so a field is set on the modem object with the full timeout.
#
# In any case, timeouts here are to catch broken/bad hardware or massive driver
# bugs rather than commonplace issues.
#
_CMD_BUSY_TIMEOUT_BASE_US = const(7000)

# Datasheet says 3.5ms needed to run a full Calibrate command (all blocks),
# however testing shows it can be as much as as 18ms.
_CALIBRATE_TYPICAL_TIME_US = const(3500)
_CALIBRATE_TIMEOUT_US = const(30000)

# Magic value used by SetRx command to indicate a continuous receive
_CONTINUOUS_TIMEOUT_VAL = const(0xFFFFFF)


class _SX126x(BaseModem):
    # common IRQ masks used by the base class functions
    _IRQ_RX_COMPLETE = _IRQ_RX_DONE | _IRQ_TIMEOUT
    _IRQ_TX_COMPLETE = _IRQ_TX_DONE

    # Common base class for SX1261, SX1262 and (pending) STM32WL55. These are all basically
    # the same except for which PA ranges are supported
    #
    # Don't construct this directly, construct lora.SX1261, lora.SX1262, lora.AsyncSX1261
    # or lora.AsyncSX1262
    def __init__(
        self,
        spi,
        cs,
        busy,
        dio1,
        dio2_rf_sw,
        dio3_tcxo_millivolts,
        dio3_tcxo_start_time_us,
        reset,
        lora_cfg,
        ant_sw,
    ):
        super().__init__(ant_sw)

        self._spi = spi
        self._cs = cs
        self._busy = busy
        self._sleep = True  # assume the radio is in sleep mode to start, will wake on _cmd
        self._dio1 = dio1

        if hasattr(busy, "init"):
            busy.init(Pin.IN)
        if hasattr(cs, "init"):
            cs.init(Pin.OUT, value=1)
        if hasattr(dio1, "init"):
            dio1.init(Pin.IN)

        self._busy_timeout = _CMD_BUSY_TIMEOUT_BASE_US + (
            dio3_tcxo_start_time_us if dio3_tcxo_millivolts else 0
        )

        self._buf_view = memoryview(bytearray(9))  # shared buffer for commands

        # These settings are kept in the object (as can't read them back from the modem)
        self._output_power = 14
        self._bw = 125
        assert self._bw_hz == 125000  # This field is set in base class, must match self._bw

        # RampTime register value
        # 0x02 is 40us, default value appears undocumented but this is the SX1276 default
        self._ramp_val = 0x02

        # Configure the SX126x at least once after reset
        self._configured = False

        if reset:
            # If the caller supplies a reset pin argument, reset the radio
            reset.init(Pin.OUT, value=0)
            time.sleep_ms(1)
            reset(1)
            time.sleep_ms(5)
        else:
            # Otherwise, at least put the radio to a known state
            self._cmd("BB", _CMD_SET_STANDBY, 0)  # STDBY_RC mode, not ready for TCXO yet

        status = self._get_status()
        if (status[0] != _STATUS_MODE_STANDBY_RC and status[0] != _STATUS_MODE_STANDBY_HSE32) or (
            status[1] > 1
        ):
            # This check exists to determine that the SPI settings and modem
            # selection are correct. Otherwise it's possible for the driver to
            # run for quite some time before it detects an invalid response.
            raise RuntimeError("Invalid initial status {}.".format(status))

        if dio2_rf_sw:
            self._cmd("BB", _CMD_SET_DIO2_AS_RF_SWITCH_CTRL, 1)

        if dio3_tcxo_millivolts:
            # Enable TCXO power via DIO3, if enabled
            #
            # timeout register is set in units of 15.625us each, use integer math
            # to calculate and round up:
            timeout = (dio3_tcxo_start_time_us * 1000 + 15624) // 15625
            if timeout < 0 or timeout > 1 << 24:
                raise ValueError("{} out of range".format("dio3_tcxo_start_time_us"))
            if dio3_tcxo_millivolts < 1600 or dio3_tcxo_millivolts > 3300:
                raise ValueError("{} out of range".format("dio3_tcxo_millivolts"))
            dv = dio3_tcxo_millivolts // 100  # 16 to 33
            tcxo_trim_lookup = (
                16,
                17,
                18,
                22,
                24,
                27,
                30,
                33,
            )  # DS Table 13-35
            while dv not in tcxo_trim_lookup:
                dv -= 1
            reg_tcxo_trim = tcxo_trim_lookup.index(dv)

            self._cmd(">BI", _CMD_SET_DIO3_AS_TCXO_CTRL, (reg_tcxo_trim << 24) + timeout)
            time.sleep_ms(15)
            # As per DS 13.3.6 SetDIO3AsTCXOCtrl, should expect error
            # value 0x20 "XOSC_START_ERR" to be flagged as XOSC has only just
            # started now. So clear it.
            self._clear_errors()

            self._check_error()

        # If DIO1 is set, mask in just the IRQs that the driver may need to be
        # interrupted by. This is important because otherwise an unrelated IRQ
        # can trigger the ISR and may not be reset by the driver, leaving DIO1 high.
        #
        # If DIO1 is not set, all IRQs can stay masked which is the power-on state.
        if dio1:
            # Note: we set both Irq mask and DIO1 mask to the same value, which is redundant
            # (one could be 0xFFFF) but may save a few bytes of bytecode.
            self._cmd(
                ">BHHHH",
                _CMD_CFG_DIO_IRQ,
                (_IRQ_RX_DONE | _IRQ_TX_DONE | _IRQ_TIMEOUT),  # IRQ mask
                (_IRQ_RX_DONE | _IRQ_TX_DONE | _IRQ_TIMEOUT),  # DIO1 mask
                0x0,  # DIO2Mask, not used
                0x0,  # DIO3Mask, not used
            )
            dio1.irq(self._radio_isr, Pin.IRQ_RISING)

        self._clear_irq()

        self._cmd("BB", _CMD_SET_PACKET_TYPE, 1)  # LoRa

        if lora_cfg:
            self.configure(lora_cfg)

    def sleep(self, warm_start=True):
        # Put the modem into sleep mode. Driver will wake the modem automatically the next
        # time an operation starts, or call standby() to wake it manually.
        #
        # If the warm_start parameter is False (non-default) then the modem will
        # lose all settings on wake. The only way to use this parameter value is
        # to destroy this modem object after calling it, and then instantiate a new
        # modem object on wake.
        #
        self._check_error()  # check errors before going to sleep because we clear on wake
        self.standby()  # save some code size, this clears the driver's rx/tx state
        self._cmd("BB", _CMD_SET_SLEEP, _flag(1 << 2, warm_start))
        self._sleep = True

    def _standby(self):
        # Send the command for standby mode.
        #
        # **Don't call this function directly, call standby() instead.**
        #
        # (This private version doesn't update the driver's internal state.)
        self._cmd("BB", _CMD_SET_STANDBY, 1)  # STDBY_XOSC mode
        self._clear_irq()  # clear IRQs in case we just cancelled a send or receive

    def is_idle(self):
        # Returns True if the modem is idle (either in standby or in sleep).
        #
        # Note this function can return True in the case where the modem has temporarily gone to
        # standby but there's a receive configured in software that will resume receiving the next
        # time poll_recv() or poll_send() is called.
        if self._sleep:
            return True  # getting status wakes from sleep
        mode, _ = self._get_status()
        return mode in (_STATUS_MODE_STANDBY_HSE32, _STATUS_MODE_STANDBY_RC)

    def _wakeup(self):
        # Wake the modem from sleep. This is called automatically the first
        # time a modem command is sent after sleep() was called to put the modem to
        # sleep.
        #
        # To manually wake the modem without initiating a new operation, call standby().
        self._cs(0)
        time.sleep_us(20)
        self._cs(1)
        self._sleep = False
        self._clear_errors()  # Clear "XOSC failed to start" which will reappear at this time
        self._check_error()  # raise an exception if any other error appears

    def _decode_status(self, raw_status, check_errors=True):
        # split the raw status, which often has reserved bits set, into the mode value
        # and the command status value
        mode = (raw_status & _STATUS_MODE_MASK) >> _STATUS_MODE_SHIFT
        cmd = (raw_status & _STATUS_CMD_MASK) >> _STATUS_CMD_SHIFT
        if check_errors and cmd in (_STATUS_CMD_EXEC_FAIL, _STATUS_CMD_ERROR):
            raise RuntimeError("Status {},{} indicates command error".format(mode, cmd))
        return (mode, cmd)

    def _get_status(self):
        # Issue the GetStatus command and return the decoded status of (mode
        # value, command status)
        #
        # Due to what appears to be a silicon bug, we send GetIrqStatus here
        # instead of GetStatus. It seems that there is some specific sequence
        # where sending command GetStatus to the chip immediately after SetRX
        # (mode 5) will trip it it into an endless TX (mode 6) for no apparent
        # reason!
        #
        # It doesn't seem to be timing dependent, all that's needed is that
        # ordering (and the modem works fine otherwise).
        #
        # As a workaround we send the GetIrqStatus command and read an extra two
        # bytes that are then ignored...
        res = self._cmd("B", _CMD_GET_IRQ_STATUS, n_read=3)[0]
        return self._decode_status(res)

    def _check_error(self):
        # Raise a RuntimeError if the radio has reported an error state.
        #
        # Return the decoded status, otherwise.
        res = self._cmd("B", _CMD_GET_ERROR, n_read=3)
        status = self._decode_status(res[0], False)
        op_error = (res[1] << 8) + res[2]
        if op_error != 0:
            raise RuntimeError("Internal radio Status {} OpError {:#x}".format(status, op_error))
        self._decode_status(res[0])  # raise an exception here if status shows an error
        return status

    def _clear_errors(self):
        # Clear any errors flagged in the modem
        self._cmd(">BH", _CMD_CLR_ERRORS, 0)

    def _clear_irq(self, clear_bits=0xFFFF):
        # Clear IRQs flagged in the modem
        #
        # By default, clears all IRQ bits. Otherwise, argument is the mask of bits to clear.
        self._cmd(">BH", _CMD_CLR_IRQ_STATUS, clear_bits)
        self._last_irq = None

    def _set_tx_ant(self, tx_ant):
        # Only STM32WL55 allows switching tx_ant from LP to HP
        raise ConfigError("tx_ant")

    def _symbol_offsets(self):
        # Called from BaseModem.get_time_on_air_us().
        #
        # This function provides a way to implement the different SF5 and SF6 in SX126x,
        # by returning two offsets: one for the overall number of symbols, and one for the
        # number of bits used to calculate the symbol length of the payload.
        return (2, -8) if self._sf in (5, 6) else (0, 0)

    def configure(self, lora_cfg):
        if self._rx is not False:
            raise RuntimeError("Receiving")

        if "preamble_len" in lora_cfg:
            self._preamble_len = lora_cfg["preamble_len"]

        self._invert_iq = (
            lora_cfg.get("invert_iq_rx", self._invert_iq[0]),
            lora_cfg.get("invert_iq_tx", self._invert_iq[1]),
            self._invert_iq[2],
        )

        if "freq_khz" in lora_cfg:
            self._rf_freq_hz = int(lora_cfg["freq_khz"] * 1000)
            rffreq = (
                self._rf_freq_hz << 25
            ) // 32_000_000  # RF-PLL frequency = 32e^6 * RFFreq / 2^25
            if not rffreq:
                raise ConfigError("freq_khz")  # set to a value too low
            self._cmd(">BI", _CMD_SET_RF_FREQUENCY, rffreq)

        if "syncword" in lora_cfg:
            syncword = lora_cfg["syncword"]
            if syncword < 0x100:
                # "Translation from SX127x to SX126x : 0xYZ -> 0xY4Z4 :
                # if you do not set the two 4 you might lose sensitivity"
                # see
                # https://www.thethingsnetwork.org/forum/t/should-private-lorawan-networks-use-a-different-sync-word/34496/15
                syncword = 0x0404 + ((syncword & 0x0F) << 4) + ((syncword & 0xF0) << 8)
            self._cmd(">BHH", _CMD_WRITE_REGISTER, _REG_LSYNCRH, syncword)

        if not self._configured or any(
            key in lora_cfg for key in ("output_power", "pa_ramp_us", "tx_ant")
        ):
            pa_config_args, self._output_power = self._get_pa_tx_params(
                lora_cfg.get("output_power", self._output_power), lora_cfg.get("tx_ant", None)
            )
            self._cmd("BBBBB", _CMD_SET_PA_CONFIG, *pa_config_args)

            if "pa_ramp_us" in lora_cfg:
                self._ramp_val = self._get_pa_ramp_val(
                    lora_cfg, [10, 20, 40, 80, 200, 800, 1700, 3400]
                )

            self._cmd("BBB", _CMD_SET_TX_PARAMS, self._output_power, self._ramp_val)

        if not self._configured or any(key in lora_cfg for key in ("sf", "bw", "coding_rate")):
            if "sf" in lora_cfg:
                self._sf = lora_cfg["sf"]
                if self._sf < _CFG_SF_MIN or self._sf > _CFG_SF_MAX:
                    raise ConfigError("sf")

            if "bw" in lora_cfg:
                self._bw = lora_cfg["bw"]

            if "coding_rate" in lora_cfg:
                self._coding_rate = lora_cfg["coding_rate"]
                if self._coding_rate < 4 or self._coding_rate > 8:  # 4/4 through 4/8, linearly
                    raise ConfigError("coding_rate")

            bw_val, self._bw_hz = {
                "7.8": (0x00, 7800),
                "10.4": (0x08, 10400),
                "15.6": (0x01, 15600),
                "20.8": (0x09, 20800),
                "31.25": (0x02, 31250),
                "41.7": (0x0A, 41700),
                "62.5": (0x03, 62500),
                "125": (0x04, 125000),
                "250": (0x05, 250000),
                "500": (0x06, 500000),
            }[str(self._bw)]

            self._cmd(
                "BBBBB",
                _CMD_SET_MODULATION_PARAMS,
                self._sf,
                bw_val,
                self._coding_rate - 4,  # 4/4=0, 4/5=1, etc
                self._get_ldr_en(),  # Note: BaseModem.get_n_symbols_x4() depends on this logic
            )

        if "rx_boost" in lora_cfg:
            # See DS Table 9-3 "Rx Gain Configuration"
            self._reg_write(_REG_RX_GAIN, 0x96 if lora_cfg["rx_boost"] else 0x94)

        self._check_error()
        self._configured = True

    def _invert_workaround(self, enable):
        # Apply workaround for DS 15.4 Optimizing the Inverted IQ Operation
        if self._invert_iq[2] != enable:
            val = self._read_read(_REG_IQ_POLARITY_SETUP)
            val = (val & ~4) | _flag(4, enable)
            self._reg_write(_REG_IQ_POLARITY_SETUP, val)
            self._invert_iq[2] = enable

    def _get_irq(self):
        # Get currently set IRQ bits.
        irq_status = self._cmd("B", _CMD_GET_IRQ_STATUS, n_read=3)
        status = self._decode_status(irq_status[0])
        flags = (irq_status[1] << 8) + irq_status[2]
        if _DEBUG:
            print("Status {} flags {:#x}".format(status, flags))
        return flags

    def calibrate(self):
        # Send the Calibrate command to the radio to calibrate RC oscillators, PLL and ADC.
        #
        # See DS 13.1.12 Calibrate Function

        # calibParam 0xFE means to calibrate all blocks.
        self._cmd("BB", _CMD_CALIBRATE, 0xFE)

        time.sleep_us(_CALIBRATE_TYPICAL_TIME_US)

        # a falling edge of BUSY indicates calibration is done
        self._wait_not_busy(_CALIBRATE_TIMEOUT_US)

    def calibrate_image(self):
        # Send the CalibrateImage command to the modem to improve reception in
        # the currently configured frequency band.
        #
        # See DS 9.2.1 Image Calibration for Specified Frequency Bands
        # and 13.1.13 CalibrateImage

        mhz = self._rf_freq_hz // 1_000_000
        if 430 <= mhz <= 440:
            args = 0x6B6F
        elif 470 <= mhz <= 510:
            args = 0x7581
        elif 779 <= mhz <= 787:
            args = 0xC1C5
        elif 863 <= mhz <= 870:
            args = 0xD7DB
        elif 902 <= mhz <= 928:
            args = 0xE1E9
        else:
            # DS says "Contact your Semtech representative for the other optimal
            # calibration settings outside of the given frequency bands"
            raise ValueError

        self._cmd(">BH", _CMD_CALIBRATE_IMAGE, args)

        # Can't find anythign in Datasheet about how long image calibration
        # takes or exactly how it signals completion. Assuming it will be
        # similar to _CMD_CALIBRATE.
        self._wait_not_busy(_CALIBRATE_TIMEOUT_US)

    def start_recv(self, timeout_ms=None, continuous=False, rx_length=0xFF):
        # Start receiving.
        #
        # Part of common low-level modem API, see README.md for usage.
        super().start_recv(timeout_ms, continuous, rx_length)  # sets _rx

        if self._tx:
            # Send is in progress and has priority, _check_recv() will start recv
            # once send finishes (caller needs to call poll_send() for this to happen.)
            if _DEBUG:
                print("Delaying receive until send completes")
            return self._dio1

        # Put the modem in a known state. It's possible a different
        # receive was in progress, this prevent anything changing while
        # we set up the new receive
        self._standby()  # calling private version to keep driver state as-is

        # Allocate the full FIFO for RX
        self._cmd("BBB", _CMD_SET_BUFFER_BASE_ADDRESS, 0xFF, 0x0)

        self._cmd(
            ">BHBBBB",
            _CMD_SET_PACKET_PARAMS,
            self._preamble_len,
            self._implicit_header,
            rx_length,  # PayloadLength, only used in implicit header mode
            self._crc_en,  # CRCType, only used in implicit header mode
            self._invert_iq[0],  # InvertIQ
        )
        self._invert_workaround(self._invert_iq[0])

        if continuous:
            timeout = _CONTINUOUS_TIMEOUT_VAL
        elif timeout_ms is not None:
            timeout = max(1, timeout_ms * 64)  # units of 15.625us
        else:
            timeout = 0  # Single receive mode, no timeout

        self._cmd(">BBH", _CMD_SET_RX, timeout >> 16, timeout)  # 24 bits

        return self._dio1

    def poll_recv(self, rx_packet=None):
        old_rx = self._rx
        rx = super().poll_recv(rx_packet)

        if rx is not True and old_rx is not False and isinstance(old_rx, int):
            # Receiving has just stopped, and a timeout was previously set.
            #
            # Workaround for errata DS 15.3 "Implicit Header Mode Timeout Behaviour",
            # which recommends to add the following after "ANY Rx with Timeout active sequence"
            self._reg_write(_REG_RTC_CTRL, 0x00)
            self._reg_write(_REG_EVT_CLR, self._reg_read(_REG_EVT_CLR) | _REG_EVT_CLR_MASK)

        return rx

    def _rx_flags_success(self, flags):
        # Returns True if IRQ flags indicate successful receive.
        # Specifically, from the bits in _IRQ_DRIVER_RX_MASK:
        # - _IRQ_RX_DONE must be set
        # - _IRQ_TIMEOUT must not be set
        # - _IRQ_CRC_ERR must not be set
        # - _IRQ_HEADER_ERR must not be set
        #
        # (Note: this is a function because the result for SX1276 depends on
        # current config, but the result is constant here.)
        return flags & _IRQ_DRIVER_RX_MASK == _IRQ_RX_DONE

    def _read_packet(self, rx_packet, flags):
        # Private function to read received packet (RxPacket object) from the
        # modem, if there is one.
        #
        # Called from poll_recv() function, which has already checked the IRQ flags
        # and verified a valid receive happened.

        ticks_ms = self._get_last_irq()

        res = self._cmd("B", _CMD_GET_RX_BUFFER_STATUS, n_read=3)
        rx_payload_len = res[1]
        rx_buffer_ptr = res[2]  # should be 0

        if rx_packet is None or len(rx_packet) != rx_payload_len:
            rx_packet = RxPacket(rx_payload_len)

        self._cmd("BB", _CMD_READ_BUFFER, rx_buffer_ptr, n_read=1, read_buf=rx_packet)

        pkt_status = self._cmd("B", _CMD_GET_PACKET_STATUS, n_read=4)

        rx_packet.ticks_ms = ticks_ms
        rx_packet.snr = pkt_status[2]  # SNR, units: dB *4
        rx_packet.rssi = 0 - pkt_status[1] // 2  # RSSI, units: dBm
        rx_packet.crc_error = (flags & _IRQ_CRC_ERR) != 0

        return rx_packet

    def prepare_send(self, packet):
        # Prepare modem to start sending. Should be followed by a call to start_send()
        #
        # Part of common low-level modem API, see README.md for usage.
        if len(packet) > 255:
            raise ConfigError("packet too long")

        # Put the modem in a known state. Any current receive is suspended at this point,
        # but calling _check_recv() will resume it later.
        self._standby()  # calling private version to keep driver state as-is

        self._check_error()

        # Set the board antenna for correct TX mode
        if self._ant_sw:
            self._ant_sw.tx(self._tx_hp())

        self._last_irq = None

        self._cmd(
            ">BHBBBB",
            _CMD_SET_PACKET_PARAMS,
            self._preamble_len,
            self._implicit_header,
            len(packet),
            self._crc_en,
            self._invert_iq[1],  # _invert_iq_tx
        )
        self._invert_workaround(self._invert_iq[1])

        # Allocate the full FIFO for TX
        self._cmd("BBB", _CMD_SET_BUFFER_BASE_ADDRESS, 0x0, 0xFF)
        self._cmd("BB", _CMD_WRITE_BUFFER, 0x0, write_buf=packet)

        # Workaround for DS 15.1 Modulation Quality with 500 kHZ LoRa Bandwidth
        # ... apparently this needs to be done "*before each packet transmission*"
        if self._bw_hz == 500_000:
            self._reg_write(0x0889, self._reg_read(0x0889) & 0xFB)
        else:
            self._reg_write(0x0889, self._reg_read(0x0889) | 0x04)

    def start_send(self):
        # Actually start a send that was loaded by calling prepare_send().
        #
        # This is split into a separate function to allow more precise timing.
        #
        # The driver doesn't verify the caller has done the right thing here, the
        # modem will no doubt do something weird if prepare_send() was not called!
        #
        # Part of common low-level modem API, see README.md for usage.

        # Currently we don't pass any TX timeout argument to the modem1,
        # which the datasheet ominously offers as "security" for the Host MCU if
        # the send doesn't start for some reason.

        self._cmd("BBBB", _CMD_SET_TX, 0x0, 0x0, 0x0)

        if _DEBUG:
            print("status {}".format(self._get_status()))
        self._check_error()

        self._tx = True

        return self._dio1

    def _wait_not_busy(self, timeout_us):
        # Wait until the radio de-asserts the busy line
        start = time.ticks_us()
        ticks_diff = 0
        while self._busy():
            ticks_diff = time.ticks_diff(time.ticks_us(), start)
            if ticks_diff > timeout_us:
                raise RuntimeError("BUSY timeout", timeout_us)
            time.sleep_us(1)
        if _DEBUG and ticks_diff > 105:
            # By default, debug log any busy time that takes longer than the
            # datasheet-promised Typical 105us (this happens when starting the 32MHz oscillator,
            # if it's turned on and off by the modem, and maybe other times.)
            print(f"BUSY {ticks_diff}us")

    def _cmd(self, fmt, *write_args, n_read=0, write_buf=None, read_buf=None):
        # Execute an SX1262 command
        # fmt - Format string suitable for use with struct.pack. First item should be 'B' and
        # corresponds to the command opcode.
        # write_args - Arguments suitable for struct.pack using fmt. First argument should be a
        # command opcode byte.
        #
        # Optional arguments:
        # write_buf - Extra buffer to write from (for FIFO writes). Mutually exclusive with n_read
        # or read_buf.
        # n_read - Number of result bytes to read back at end
        # read_buf - Extra buffer to read into (for FIFO reads)
        #
        # Returns None if n_read==0, otherwise a memoryview of length n_read which points into a
        # shared buffer (buffer will be clobbered on next call to _cmd!)
        if self._sleep:
            self._wakeup()

        # Ensure "busy" from previously issued command has de-asserted. Usually this will
        # have happened well before _cmd() is called again.
        self._wait_not_busy(self._busy_timeout)

        # Pack write_args into slice of _buf_view memoryview of correct length
        wrlen = struct.calcsize(fmt)
        assert n_read + wrlen <= len(self._buf_view)  # if this fails, make _buf bigger!
        struct.pack_into(fmt, self._buf_view, 0, *write_args)
        buf = self._buf_view[: (wrlen + n_read)]

        if _DEBUG:
            print(">>> {}".format(buf[:wrlen].hex()))
            if write_buf:
                print(">>> {}".format(write_buf.hex()))
        self._cs(0)
        self._spi.write_readinto(buf, buf)
        if write_buf:
            self._spi.write(write_buf)  # Used by _CMD_WRITE_BUFFER only
        if read_buf:
            self._spi.readinto(read_buf, 0xFF)  # Used by _CMD_READ_BUFFER only
        self._cs(1)

        if n_read > 0:
            res = self._buf_view[wrlen : (wrlen + n_read)]  # noqa: E203
            if _DEBUG:
                print("<<< {}".format(res.hex()))
            return res

    def _reg_read(self, addr):
        return self._cmd(">BHB", _CMD_READ_REGISTER, addr, 0, n_read=1)[0]

    def _reg_write(self, addr, val):
        return self._cmd(">BHB", _CMD_WRITE_REGISTER, addr, val & 0xFF)


class _SX1262(_SX126x):
    # Don't construct this directly, construct lora.SX1262 or lora.AsyncSX1262
    def __init__(
        self,
        spi,
        cs,
        busy,
        dio1=None,
        dio2_rf_sw=True,
        dio3_tcxo_millivolts=None,
        dio3_tcxo_start_time_us=1000,
        reset=None,
        lora_cfg=None,
        ant_sw=None,
    ):
        super().__init__(
            spi,
            cs,
            busy,
            dio1,
            dio2_rf_sw,
            dio3_tcxo_millivolts,
            dio3_tcxo_start_time_us,
            reset,
            lora_cfg,
            ant_sw,
        )

        # Apply workaround for DS 15.2 "Better Resistance of the SX1262 Tx to Antenna Mismatch
        self._reg_write(0x8D8, self._reg_read(0x8D8) | 0x1E)

    def _tx_hp(self):
        # SX1262 has High Power only (deviceSel==0)
        return True

    def _get_pa_tx_params(self, output_power, tx_ant):
        # Given an output power level in dB, return a 2-tuple:
        # - First item is the 3 arguments for SetPaConfig command
        # - Second item is the power level argument value for SetTxParams command.
        #
        # DS 13.1.14.1 "PA Optimal Settings" gives optimally efficient
        # values for output power +22, +20, +17, +14 dBm and "these changes make
        # the use of nominal power either sub-optimal or unachievable" (hence it
        # recommends setting +22dBm nominal TX Power for all these).
        #
        # However the modem supports output power as low as -9dBm, and there's
        # no explanation in the datasheet of how to best set other output power
        # levels.
        #
        # Semtech's own driver (sx126x.c in LoRaMac-node) only ever executes
        # SetPaConfig with the values shown in the datasheet for +22dBm, and
        # then executes SetTxParams with power set to the nominal value in
        # dBm.
        #
        # Try for best of both worlds here: If the caller requests an "Optimal"
        # value, use the datasheet values. Otherwise set nominal power only as
        # per Semtech's driver.
        output_power = int(_clamp(output_power, -9, 22))

        DEFAULT = (0x4, 0x7, 0x0, 0x1)
        OPTIMAL = {
            22: (DEFAULT, 22),
            20: ((0x3, 0x5, 0x0, 0x1), 22),
            17: ((0x2, 0x3, 0x0, 0x1), 22),
            14: ((0x2, 0x2, 0x0, 0x1), 22),
        }
        if output_power in OPTIMAL:
            # Datasheet optimal values
            return OPTIMAL[output_power]
        else:
            # Nominal values, as per Semtech driver
            return (DEFAULT, output_power & 0xFF)


class _SX1261(_SX126x):
    # Don't construct this directly, construct lora.SX1261, or lora.AsyncSX1261
    def __init__(
        self,
        spi,
        cs,
        busy,
        dio1=None,
        dio2_rf_sw=True,
        dio3_tcxo_millivolts=None,
        dio3_tcxo_start_time_us=1000,
        reset=None,
        lora_cfg=None,
        ant_sw=None,
    ):
        super().__init__(
            spi,
            cs,
            busy,
            dio1,
            dio2_rf_sw,
            dio3_tcxo_millivolts,
            dio3_tcxo_start_time_us,
            reset,
            lora_cfg,
            ant_sw,
        )

    def _tx_hp(self):
        # SX1261 has Low Power only (deviceSel==1)
        return False

    def _get_pa_tx_params(self, output_power, tx_ant):
        # Given an output power level in dB, return a 2-tuple:
        # - First item is the 3 arguments for SetPaConfig command
        # - Second item is the power level argument value for SetTxParams command.
        #
        # As noted above for SX1262, DS 13.1.14.1 "PA Optimal Settings"
        # gives optimally efficient values for output power +15, +14, +10 dBm
        # but nothing specific to the other power levels (down to -17dBm).
        #
        # Therefore do the same as for SX1262 to set optimal values if known, nominal otherwise.
        output_power = _clamp(int(output_power), -17, 15)

        DEFAULT = (0x4, 0x0, 0x1, 0x1)
        OPTIMAL = {
            15: ((0x06, 0x0, 0x1, 0x1), 14),
            14: (DEFAULT, 14),
            10: ((0x1, 0x0, 0x1, 0x1), 13),
        }

        if output_power == 15 and self._rf_freq_hz < 400_000_000:
            # DS 13.1.14.1 has Note that PaDutyCycle is limited to 0x4 below 400MHz,
            # so disallow the 15dBm optimal setting.
            output_power = 14

        if output_power in OPTIMAL:
            # Datasheet optimal values
            return OPTIMAL[output_power]
        else:
            # Nominal values, as per Semtech driver
            return (DEFAULT, output_power & 0xFF)


# Define the actual modem classes that use the SyncModem & AsyncModem "mixin-like" classes
# to create sync and async variants.

try:
    from .sync_modem import SyncModem

    class SX1261(_SX1261, SyncModem):
        pass

    class SX1262(_SX1262, SyncModem):
        pass

except ImportError:
    pass

try:
    from .async_modem import AsyncModem

    class AsyncSX1261(_SX1261, AsyncModem):
        pass

    class AsyncSX1262(_SX1262, AsyncModem):
        pass

except ImportError:
    pass
