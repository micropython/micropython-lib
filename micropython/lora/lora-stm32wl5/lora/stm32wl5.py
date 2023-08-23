# MicroPython LoRa STM32WL55 embedded sub-ghz radio driver
# MIT license; Copyright (c) 2022 Angus Gratton
#
# This driver is essentially an embedded SX1262 with a custom internal interface block.
# Requires the stm module in MicroPython to be compiled with STM32WL5 subghz radio support.
#
# LoRa is a registered trademark or service mark of Semtech Corporation or its affiliates.
from machine import Pin, SPI
import stm
from . import sx126x
from micropython import const

_CMD_CLR_ERRORS = const(0x07)

_REG_OCP = const(0x8E7)

# Default antenna switch config is as per Nucleo WL-55 board. See UM2592 Fig 18.
# Possible to work with other antenna switch board configurations by passing
# different ant_sw_class arguments to the modem, any class that creates an object with rx/tx


class NucleoWL55RFConfig:
    def __init__(self):
        self._FE_CTRL = (Pin(x, mode=Pin.OUT) for x in ("C4", "C5", "C3"))

    def _set_fe_ctrl(self, values):
        for pin, val in zip(self._FE_CTRL, values):
            pin(val)

    def rx(self):
        self._set_fe_ctrl((1, 0, 1))

    def tx(self, hp):
        self._set_fe_ctrl((0 if hp else 1, 1, 1))

    def idle(self):
        pass


class DIO1:
    # Dummy DIO1 "Pin" wrapper class to pass to the _SX126x class
    def irq(self, handler, _):
        stm.subghz_irq(handler)


class _WL55SubGhzModem(sx126x._SX126x):
    # Don't construct this directly, construct lora.WL55SubGhzModem or lora.AsyncWL55SubGHzModem
    def __init__(
        self,
        lora_cfg=None,
        tcxo_millivolts=1700,
        ant_sw=NucleoWL55RFConfig,
    ):
        self._hp = False

        if ant_sw == NucleoWL55RFConfig:
            # To avoid the default argument being an object instance
            ant_sw = NucleoWL55RFConfig()

        super().__init__(
            # RM0453 7.2.13 says max 16MHz, but this seems more stable
            SPI("SUBGHZ", baudrate=8_000_000),
            stm.subghz_cs,
            stm.subghz_is_busy,
            DIO1(),
            False,  # dio2_rf_sw
            tcxo_millivolts,  # dio3_tcxo_millivolts
            10_000,  # dio3_tcxo_start_time_us, first time after POR is quite long
            None,  # reset
            lora_cfg,
            ant_sw,
        )

    def _clear_errors(self):
        # A weird difference between STM32WL55 and SX1262, WL55 only takes one
        # parameter byte for the Clr_Error() command compared to two on SX1262.
        # The bytes are always zero in both cases.
        #
        # (Not clear if sending two bytes will also work always/sometimes, but
        # sending one byte to SX1262 definitely does not work!
        self._cmd("BB", _CMD_CLR_ERRORS, 0x00)

    def _clear_irq(self, clear_bits=0xFFFF):
        super()._clear_irq(clear_bits)
        # SUBGHZ Radio IRQ requires manual re-enabling after interrupt
        stm.subghz_irq(self._radio_isr)

    def _tx_hp(self):
        # STM32WL5 supports both High and Low Power antenna pins depending on tx_ant setting
        return self._hp

    def _get_pa_tx_params(self, output_power, tx_ant):
        # Given an output power level in dBm and the tx_ant setting (if any),
        # return settings for SetPaConfig and SetTxParams.
        #
        # ST document RM0453 Set_PaConfig() reference and accompanying Table 35
        # show values that are an exact superset of the SX1261 and SX1262
        # available values, depending on which antenna pin is to be
        # used. Therefore, call either modem's existing _get_pa_tx_params()
        # function depending on the current tx_ant setting (default is low
        # power).

        if tx_ant is not None:
            # Note: currently HP antenna power output is less than it should be,
            # due to some (unknown) bug.
            self._hp = tx_ant == "PA_BOOST"

        # Update the OCP register to match the maximum power level
        self._reg_write(_REG_OCP, 0x38 if self._hp else 0x18)

        if self._hp:
            return sx126x._SX1262._get_pa_tx_params(self, output_power, tx_ant)
        else:
            return sx126x._SX1261._get_pa_tx_params(self, output_power, tx_ant)


# Define the actual modem classes that use the SyncModem & AsyncModem "mixin-like" classes
# to create sync and async variants.

try:
    from .sync_modem import SyncModem

    class WL55SubGhzModem(_WL55SubGhzModem, SyncModem):
        pass

except ImportError:
    pass

try:
    from .async_modem import AsyncModem

    class AsyncWL55SubGhzModem(_WL55SubGhzModem, AsyncModem):
        pass

except ImportError:
    pass
