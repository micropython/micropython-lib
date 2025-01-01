"""MIT License

Copyright (c) 2024 Marco Miano

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.




Microchip MCP9808 driver for MicroPython

THE MCP9808 IS A COMPLEX SENSOR WITH MANY FEATURES. IS IT ADVISABLE TO READ THE DATASHEET.

DO NOT ACCESS REGISTERS WITH ADDRESSES HIGHER THAN 0x08 AS THEY CONTAIN CALIBRATION CODES.
DOING SO MAY IRREPARABLY DAMAGE THE SENSOR.

This driver is a comprehensive implementation of the MCP9808 sensor's features. It is designed
to be easy to use and offers a high level of abstraction from the sensor's registers.
The driver includes built-in error checking (such as type validation and bounds checking
for register access) and a debug mode to assist with development.



Example usage:

from mcp9808 import MCP9808, HYST_15, RES_0_125
from machine import SoftI2C, Pin

i2c = SoftI2C(scl=Pin(17), sda=Pin(16), freq=400000)
t_sensor = MCP9808(i2c)

# Get temeperature with deafult settings
temperature: float = t_sensor.get_temperature()

# Various settings
t_sensor.set_hysteresis_mode(hyst_mode=HYST_15)
t_sensor.set_resolution(resolution=RES_0_125)
t_sensor.set_alert_crit_limit(crit_limit=65.0)
t_sensor.set_alert_upper_limit(upper_limit=50.0)
t_sensor.set_alert_lower_limit(lower_limit=-10.0)
t_sensor.enable_alert()

# Enable debug mode to get warnings
t_sensor._debug = True


# For more information, see the README file at
https://github.com/MarcoMiano/mip-mcp9808
"""

from machine import SoftI2C, I2C

# Handy Constants
HYST_00 = 0b00  # Hysteresis 0°C (power-up default)
HYST_15 = 0b01  # Hysteresis 1,5°C
HYST_30 = 0b10  # Hysteresis 3,0°C
HYST_60 = 0b11  # Hysteresis 6,0°C

RES_0_5 = 0b00  # Resolution 0.5°C
RES_0_25 = 0b01  # Resolution 0.25°C
RES_0_125 = 0b10  # Resolution 0.125°C
RES_0_0625 = 0b11  # Resolution 0.0625°C (power-up default)


class MCP9808(object):
    """A class to interface with the Microchip MCP9808 temperature sensor over I2C.

    Attributes:
        ``BASE_ADDR`` (int): The base I2C address for the MCP9808 sensor.
        ``REG_CFG`` (int): Address of the configuration register.
        ``REG_ATU`` (int): Address of the alert temperature upper boundary trip register.
        ``REG_ATL`` (int): Address of the alert temperature lower boundary trip register.
        ``REG_ATC`` (int): Address of the critical temperature trip register.
        ``REG_TEM`` (int): Address of the temperature register.
        ``REG_MFR`` (int): Address of the manufacturer ID register.
        ``REG_DEV`` (int): Address of the device ID register.
        ``REG_RES`` (int): Address of the resolution register.
    """

    BASE_ADDR = 0x18
    #######################################################
    # DON'T ACCESS REGISTER WITH ADDRESS HIGHER THAN 0X08 #
    #######################################################
    REG_CFG = 0x01  # Config register
    REG_ATU = 0x02  # Alert Temperature Upper boundary trip register
    REG_ATL = 0x03  # Alert Temperature Lower boundary trip register
    REG_ATC = 0x04  # Critical Temperature Trip register
    REG_TEM = 0x05  # Temperature register
    REG_MFR = 0x06  # Manufacturer ID register
    REG_DEV = 0x07  # Device ID register
    REG_RES = 0x08  # Resolution register

    def __init__(
        self,
        i2c: SoftI2C | I2C,
        addr: int | None = None,
        A0: bool = False,
        A1: bool = False,
        A2: bool = False,
        debug: bool = False,
    ) -> None:
        """Initialize the sensor object instance.

        Args:
            ``i2c`` (SoftI2C | I2C): The I2C bus instance to use for communication.
            ``addr`` (int | None, optional): The I2C address of the sensor. If not provided,
                the address will be calculated based on A0, A1, and A2. Defaults to None.
            ``A0`` (bool, optional): The state of address pin A0. Defaults to False.
            ``A1`` (bool, optional): The state of address pin A1. Defaults to False.
            ``A2`` (bool, optional): The state of address pin A2. Defaults to False.
            ``debug`` (bool, optional): Enable or disable debug mode. Defaults to False.
        Returns:
            ``None``
        """

        self._i2c: SoftI2C | I2C = i2c
        self._debug: bool = debug
        if addr:
            self._addr = addr
        else:
            self._addr: int = self.BASE_ADDR | (A2 << 2) | (A1 << 1) | A0
        self._check_device()
        self._get_config()

    def _check_device(self) -> None:
        """Checks the device's manufacturer ID and device ID to ensure it is the correct device.

        Raises:
            ``Exception``: If the manufacturer ID does not match the expected value.
            ``Exception``: If the device ID does not match the expected value.
        Warns:
            If the hardware revision does not match the expected value and debug mode is enabled.
        Returns:
            ``None``
        """

        self._mfr_id: bytes = self._i2c.readfrom_mem(self._addr, self.REG_MFR, 2)
        if self._mfr_id != b"\x00\x54":
            raise Exception(f"Invalid manufacturer ID {self._mfr_id}")
        self._dev_id: bytes = self._i2c.readfrom_mem(self._addr, self.REG_DEV, 2)
        if self._dev_id[0] != 4:
            raise Exception(f"Invalid device ID {self._dev_id[0]}")
        if self._dev_id[1] != 0 and self._debug:
            print(
                f"[WARN] Module written for HW revision 0 but got {self._dev_id[1]}.",
            )

    def _get_config(self) -> None:
        """Private method to read the configuration register from the sensor.

        This method reads 2 bytes from the configuration register of the sensor.
        It then parses the bytes to update the following instance attributes:
            ``_hyst_mode``: Hysteresis mode (int)
            ``_shdn``: Shutdown mode (bool)
            ``_crit_lock``: Critical temperature register lock (bool)
            ``_alerts_lock``: Alerts temperature registers lock (bool)
            ``_irq_clear_bit``: Interrupt clear bit (bool)
            ``_alert``: Alert output status (bool)
            ``_alert_ctrl``: Alert control (bool)
            ``_alert_sel``: Alert output select (bool)
            ``_alert_pol``: Alert output polarity (bool)
            ``_alert_mode``: Alert output mode (bool)
        Returns:
            ``None``
        """

        buf: bytes = self._i2c.readfrom_mem(self._addr, self.REG_CFG, 2)
        self._hyst_mode: int = (buf[0] >> 1) & 0x03
        self._shdn = bool(buf[0] & 0x01)
        self._crit_lock = bool(buf[1] & 0x80)
        self._alerts_lock = bool(buf[1] & 0x40)
        self.irq_clear_bit = bool(buf[1] & 0x20)
        self._alert = bool(buf[1] & 0x10)
        self._alert_ctrl = bool(buf[1] & 0x08)
        self._alert_sel = bool(buf[1] & 0x04)
        self.alert_pol = bool(buf[1] & 0x02)
        self._alert_mode = bool(buf[1] & 0x01)

    def _set_config(
        self,
        hyst_mode: int | None = None,
        shdn: bool | None = None,
        crit_lock: bool | None = None,
        alerts_lock: bool | None = None,
        irq_clear_bit: bool = False,
        alert_ctrl: bool | None = None,
        alert_sel: bool | None = None,
        alert_pol: bool | None = None,
        alert_mode: bool | None = None,
    ) -> None:
        """Private method to set the configuration of the sensor.

        Parameters:
            ``hyst_mode`` (int | None): Hysteresis mode. Valid values are HYST_00, HYST_15, HYST_30, HYST_60.
            ``shdn (bool`` | None): Shutdown mode.
            ``crit_lock`` (bool | None): Critical temperature register lock.
            ``alerts_lock`` (bool | None): Alerts temperature registers lock.
            ``irq_clear``_bit (bool): Interrupt clear bit.
            ``alert_ctrl`` (bool | None): Alert output control.
            ``alert_sel`` (bool | None): Alert output select.
            ``alert_pol`` (bool | None): Alert output polarity.
            ``alert_mode`` (bool | None): Alert output mode.
        Raises:
            ``ValueError``: If hyst_mode is not one of the valid values.
            ``TypeError``: If any of the boolean parameters are not of type bool.
        Returns:
            ``None``
        """

        if hyst_mode is None:
            hyst_mode = self._hyst_mode
        if shdn is None:
            shdn = self._shdn
        if crit_lock is None:
            crit_lock = self._crit_lock
        if alerts_lock is None:
            alerts_lock = self._alerts_lock
        if alert_ctrl is None:
            alert_ctrl = self._alert_ctrl
        if alert_sel is None:
            alert_sel = self._alert_sel
        if alert_pol is None:
            alert_pol = self.alert_pol
        if alert_mode is None:
            alert_mode = self._alert_mode

        # Type/value check the parameters
        if hyst_mode not in [HYST_00, HYST_15, HYST_30, HYST_60]:
            raise ValueError(
                f"hyst_mode: {hyst_mode}. Value should be between 0 and 3 inclusive."
            )
        if shdn.__class__ != bool:
            raise TypeError(
                f"shdn: {shdn} {shdn.__class__}. Expecting a bool.",
            )
        if crit_lock.__class__ != bool:
            raise TypeError(
                f"crit_lock: {crit_lock} {crit_lock.__class__}. Expecting a bool.",
            )
        if alerts_lock.__class__ != bool:
            raise TypeError(
                f"alerts_lock: {alerts_lock} {alerts_lock.__class__}. Expecting a bool.",
            )
        if irq_clear_bit.__class__ != bool:
            raise TypeError(
                f"irq_clear_bit: {irq_clear_bit} {irq_clear_bit.__class__}. Expecting a bool.",
            )
        if alert_ctrl.__class__ != bool:
            raise TypeError(
                f"alert_ctrl: {alert_ctrl} {alert_ctrl.__class__}. Expecting a bool.",
            )
        if alert_sel.__class__ != bool:
            raise TypeError(
                f"alert_sel: {alert_sel} {alert_sel.__class__}. Expecting a bool.",
            )
        if alert_pol.__class__ != bool:
            raise TypeError(
                f"alert_pol: {alert_pol} {alert_pol.__class__}. Expecting a bool.",
            )
        if alert_mode.__class__ != bool:
            raise TypeError(
                f"alert_mode: {alert_mode} {alert_mode.__class__}. Expecting a bool.",
            )

        # Build the send buffer
        buf = bytearray(b"\x00\x00")
        buf[0] = (hyst_mode << 1) | shdn
        buf[1] = (
            (crit_lock << 7)
            | (alerts_lock << 6)
            | (irq_clear_bit << 5)
            | (alert_ctrl << 3)
            | (alert_sel << 2)
            | (alert_pol << 1)
            | alert_mode
        )
        # Write the buffer to the sensor
        self._i2c.writeto_mem(self._addr, self.REG_CFG, buf)
        self._get_config()
        # Check if the configuration was set correctly id debug mode is enabled
        if self._debug:
            if self._hyst_mode != hyst_mode:
                print(
                    f"[WARN] Failed to set hyst_mode. Set {hyst_mode} got {self._hyst_mode}",
                )
            if self._shdn != shdn:
                print(
                    f"[WARN] Failed to set shdn. Set {shdn} got {self._shdn}",
                )
            if self._crit_lock != crit_lock:
                print(
                    f"[WARN] Failed to set crit_lock. Set {crit_lock} got {self._crit_lock}",
                )
            if self.irq_clear_bit:
                print(
                    "[WARN] Something wrong with irq_clear_bit. Should always read False"
                )
            if self._alerts_lock != alerts_lock:
                print(
                    f"[WARN] Failed to set alerts_lock. Set {alerts_lock} got {self._alerts_lock}",
                )
            if self._alert_ctrl != alert_ctrl:
                print(
                    f"[WARN] Failed to set alert_ctrl. Set {alert_ctrl} got {self._alert_ctrl}.",
                )
            if self._alert_sel != alert_sel:
                print(
                    f"[WARN] Failed to set alert_sel. Set {alert_sel} got {self._alert_sel}.",
                )
            if self.alert_pol != alert_pol:
                print(
                    f"[WARN] Failed to set alert_pol. Set {alert_pol} got {self.alert_pol}.",
                )
            if self._alert_mode != alert_mode:
                print(
                    f"[WARN] Failed to set alert_mode. Set {alert_mode} got {self._alert_mode}.",
                )

    def _set_alert_limit(self, limit: float, register: int) -> None:
        """Private method to set the alert limit register.

        Inteded to be used by the set_alert_XXXXX_limit wrapper methods.
        Args:
            ``limit`` (float | int): The temperature limit to set. Must be between -128 and 127.
            ``register`` (int): The register address to write the limit to.
        Raises:
            ``TypeError``: If the limit is not a float or int.
            ``ValueError``: If the limit is out of the range [-128, 127].
            ``ValueError``: If the register address is not valid.
        Debug:
            - Issue a warning if the threshold is outside of the operational range.
            - Issue a warning if the alert limit was not set correctly.
        Returns:
            ``None``
        """

        if limit.__class__ not in [float]:
            raise TypeError(
                f"limit: {limit} {limit.__class__}. Expecting float|int.",
            )
        if limit < -128 or limit > 127:
            raise ValueError("Temperature out of range [-128, 127]")
        if (limit < -40 or limit > 125) and self._debug:
            print(
                "[WARN] Temperature outside of operational range, limit won't be ever reached.",
            )
        if register not in [self.REG_ATU, self.REG_ATL, self.REG_ATC]:
            raise ValueError(f"Invalid register address {register}")

        buf = bytearray(b"\x00\x00")

        # If limit is negative set sign fifth bit ON otherwise leave it OFF
        if limit < 0:
            sign = 0x10
        else:
            sign = 0x00

        # If limit is between -1 and 0 (like -0.25) set integral to 0xFF (-0 in 2's complement)
        if -1 < limit < 0:
            integral: int = 0xFF
        # Otherwise truncate limit to a int and keep only the rightmost byte
        else:
            integral: int = int(limit) & 0xFF

        # Calculate the fractional part by keeping the 2 rightmost bits of the integer division
        # of 0.25 (the sensitivity) and the remainder part of the decimal part of limit
        frac_normal: int = int((limit - integral) / 0.25) & 0x03

        # Build the send buffer highest byte combining (bitwise-or) sign and the integral
        # right-shifted by 4
        buf[0] = sign | (integral >> 4)
        # Build the send buffer lowest byte combining (bitwise-or) the integral
        # left-shifted by 4 and the fractional part left shifted by 2 (last 2 bit are 0)
        buf[1] = (integral << 4) | (frac_normal << 2)

        self._i2c.writeto_mem(self._addr, register, buf)

        if self._debug:
            check: bytes = self._i2c.readfrom_mem(self._addr, register, 2)
            if check != buf:
                print(
                    f"[WARN] Failed to set alert limit. Set {buf[0]:08b}-{buf[1]:08b}",
                    f"but got {check[0]:08b}-{check[1]:08b}",
                )

    def shutdown(self) -> None:
        """Put the sensor in low power mode.

        Returns:
            ``None``
        """
        self._set_config(shdn=True)

    def wake(self) -> None:
        """Wake the sensor from low power mode.

        Returns:
            ``None``
        """
        self._set_config(shdn=False)

    def lock_crit_limit(self) -> None:
        """Locks the critical temperature limit.

        When the critical temperature limit is locked, it cannot be changed
        until the sensor is power cycled.
        Returns:
            ``None``
        """
        self._set_config(crit_lock=True)

    def lock_alerts_limit(self) -> None:
        """Locks the alerts limits.

        When the alerts limits are locked, they cannot be changed
        until the sensor is power cycled.
        Returns:
            ``None``
        """
        self._set_config(alerts_lock=True)

    def irq_clear(self) -> None:
        """Clears the interrupt output.

        This method clears the interrupt output.
        Returns:
            ``None``
        """
        self._set_config(irq_clear_bit=True)

    def get_alert_status(self) -> bool:
        """Get the alert status.

        This method reads the alert status from the sensor.
        Returns:
            ``bool``: The alert status.
        """
        self._get_config()
        return self.alert

    def enable_alert(self) -> None:
        """Enable the alert output.

        Returns:
            ``None``
        """
        self._set_config(alert_ctrl=True)

    def disable_alert(self) -> None:
        """Disable the alert output.

        Returns:
            ``None``
        """
        self._set_config(alert_ctrl=False)

    def set_alert_threshold(self, only_crit=False) -> None:
        """Set the alert output select.

        Select if the alert output should be activated only by the critical limit or both critical
        and upper/lower limits.
        Args:
            ``only_crit`` (bool, optional): Set the alert output to only critical. Defaults to False.
        Returns:
            ``None``
        """
        self._set_config(alert_sel=only_crit)

    def set_alert_polarity(self, active_high=False) -> None:
        """Set the alert output polarity.

        Set the alert output polarity to active high or active low.
        Args:
            ``active_high`` (bool, optional): Set the alert output polarity to active high.
                                          Defaults to False.
        Returns:
            ``None``
        """
        self._set_config(alert_pol=active_high)

    def set_alert_mode(self, irq=False) -> None:
        """Set the alert output mode.

        Set the alert output mode to interrupt or comparator.
        Args:
            ``irq`` (bool, optional): Set the alert output mode to interrupt. Defaults to False.
        Returns:
            ``None``
        """
        self._set_config(alert_mode=irq)

    def set_alert_upper_limit(self, upper_limit: float) -> None:
        """Set the alert upper limit.

        Args:
            upper_limit (float | int): The upper limit to set.
                                       It will rounded to the nearest 0.25°C.
        Raises:
            ``TypeError``: If the limit is not a float or int.
            ``ValueError``: If the limit is out of the range [-128, 127].
        Debug:
            - Issue a warning if the threshold is outside of the operational range.
            - Issue a warning if the alert limit was not set correctly.
        Returns:
            ``None``
        """
        self._set_alert_limit(upper_limit, self.REG_ATU)

    def set_alert_lower_limit(self, lower_limit: float) -> None:
        """Set the alert lower limit.

        Args:
            lower_limit (float | int): The lower limit to set.
        Raises:
            ``TypeError``: If the limit is not a float or int.
            ``ValueError``: If the limit is out of the range [-128, 127].
        Debug:
            - Issue a warning if the threshold is outside of the operational range.
            - Issue a warning if the alert limit was not set correctly.
        Returns:
            ``None``
        """
        self._set_alert_limit(lower_limit, self.REG_ATL)

    def set_alert_crit_limit(self, crit_limit: float) -> None:
        """Set the alert critical limit.

        Args:
            crit_limit (float | int): The critical limit to set.
        Raises:
            ``TypeError``: If the limit is not a float or int.
            ``ValueError``: If the limit is out of the range [-128, 127].
        Debug:
            - Issue a warning if the threshold is outside of the operational range.
            - Issue a warning if the alert limit was not set correctly.
        Returns:
            ``None``
        """
        self._set_alert_limit(crit_limit, self.REG_ATC)

    def get_temperature(self) -> float:
        """Get the temperature from the sensor.

        Returns:
            ``float``: The temperature in degrees Celsius.
        """
        # Read temperature register from sensor
        buf: bytes = self._i2c.readfrom_mem(self._addr, self.REG_TEM, 2)
        # Extract the sign bit
        sign: int = buf[0] & 0x10
        # Calculate the 4 upper bit of the integral by left shifting the first byte by 4
        upper: int = (buf[0] << 4) & 0xFF
        # Calculate the 4 lower bit of the integral and the fractional part into a float
        # dividing by 16 the second buf byte
        lower: float = (buf[1] & 0xFF) / 16
        # Calculate the temperature as a float, adding the upper byte (leftmost 4 bit of integral)
        # and the lower byte (rightmost 4 bit of integral + fractional).
        # In case of negative value subtract 256 from the sum to convert from 2's complement 8+4bit
        # fractional value to negative float
        temp: float = (upper + lower) - 256 if sign else upper + lower
        return temp

    def get_alert_triggers(self) -> tuple[bool, bool, bool]:
        """Get the alert triggers.

        Trigger bits are not influenced by the alert output mode (compare or interrupt) or by the
        alert polarity (active high or active low) or by the alert control (enable or disable).
        Returns:
            ``tuple[bool, bool, bool]``: A tuple containing the alert triggers.
                The first element is True if the temperature is greater or equal to the critical
                limit.
                The second element is True if the temperature is greater than the upper limit.
                The third element is True if the temperature is less than the lower limit.
        """
        # Read temperature register from sensor
        buf: bytes = self._i2c.readfrom_mem(self._addr, self.REG_TEM, 2)
        # Extract the 16th bit (last), Ta vs. Tcrit.    False = Ta < Tcrit   | True = Ta >= Tcrit
        ta_tcrit = bool(buf[0] & 0x80)
        # Extract the 15th bit, Ta vs. Tupper.          False = Ta <= Tupper | True = Ta > Tupper
        ta_tupper = bool(buf[0] & 0x40)
        # Extract the 14th bit, Ta vs Tlower.           False = Ta >= Tlower | True = Ta < Tlower
        ta_tlower = bool(buf[0] & 0x20)

        return ta_tcrit, ta_tupper, ta_tlower

    def set_resolution(self, resolution=RES_0_0625) -> None:
        """Set the resolution of the sensor.

        Args:
            resolution (int, optional): The resolution to set.
                Valid values are RES_0_5, RES_0_25, RES_0_125, RES_0_0625.
                Defaults to RES_0_0625.
        Raises:
            ValueError: If the resolution is not a valid value.
        Debug:
            - Issue a warning if the resolution was not set correctly.
        Returns:
            ``None``
        """
        # Check if resolution is a compatible value
        if resolution not in [RES_0_5, RES_0_25, RES_0_125, RES_0_0625]:
            raise ValueError(
                f"Invalid resolution: {resolution}. Value should be between 0 and 3 inclusive.",
            )

        buf = bytearray(b"\x00")

        buf[0] |= resolution & 0x03
        self._i2c.writeto_mem(self._addr, self.REG_RES, buf)
        if self._debug:
            check = self._i2c.readfrom_mem(self._addr, self.REG_RES, 1)
            if check != buf:
                print(
                    f"[WARN] Failed to set resolution. Set {resolution} got {check[0]}"
                )

    @property
    def hyst_mode(self) -> int:
        """Get the hysteresis mode.

        Returns:
            ``int``: The hysteresis mode.
        """
        self._get_config()
        return self._hyst_mode

    @hyst_mode.setter
    def hyst_mode(self, hyst_mode: int) -> None:
        """Set the hysteresis mode.

        Args:
            ``hyst_mode`` (int): The hysteresis mode to set.
                Valid values are HYST_00, HYST_15, HYST_30, HYST_60.
        """
        self._set_config(hyst_mode=hyst_mode)

    @property
    def shdn(self) -> bool:
        """Get the shutdown mode.

        Returns:
            ``bool``: The shutdown mode.
        """
        self._get_config()
        return self._shdn

    @property
    def crit_lock(self) -> bool:
        """Get the critical temperature register lock.

        Returns:
            ``bool``: The critical temperature register lock.
        """
        self._get_config()
        return self._crit_lock

    @property
    def alerts_lock(self) -> bool:
        """Get the alerts temperature registers lock.

        Returns:
            ``bool``: The alerts temperature registers lock.
        """
        self._get_config()
        return self._alerts_lock

    @property
    def alert(self) -> bool:
        """Get the alert control.

        Returns:
            ``bool``: The alert control.
        """
        self._get_config()
        return self._alert

    @property
    def alert_ctrl(self) -> bool:
        """Get the alert control.

        Returns:
            ``bool``: The alert control.
        """
        self._get_config()
        return self._alert_ctrl

    @property
    def alert_sel(self) -> bool:
        """Get the alert output select.

        Returns:
            ``bool``: The alert output select.
        """
        self._get_config()
        return self._alert_sel

    @property
    def alert_mode(self) -> bool:
        """Get the alert output mode.

        Returns:
            ``bool``: The alert output mode.
        """
        self._get_config()
        return self._alert_mode
