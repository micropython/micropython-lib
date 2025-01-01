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




Microchip MCP9808 driver/sensor test suite for MicroPython

THE MCP9808 IS A COMPLEX SENSOR WITH MANY FEATURES. IS IT ADVISABLE TO READ THE DATASHEET.

DO NOT ACCESS REGISTERS WITH ADDRESSES HIGHER THAN 0x08 AS THEY CONTAIN CALIBRATION CODES.
DOING SO MAY IRREPARABLY DAMAGE THE SENSOR.

This test suite is designed to check the correct operation of the MCP9808 sensor driver and the 
sensor itself. It is advisable to run this test suite if anything is changed in the driver code,
or if the sensor is not behaving right.
This test suite is written and tested on a Raspberry Pi Pico W Board with MicroPython v1.24.1.



Pin connections:
    - POWER: pin15 
             The sensor is powered from a GPIO pin to be able to power cycle the sensor during the 
             tests.
             CHECK THAT YOUR GPIO PIN CAN SUPPLY ENOUGH CURRENT AND VOLTAGE TO POWER THE SENSOR. 
             (2.7V-5.5V AT 0.4mA)
    - SDA:   pin16
    - SCL:   pin17
    - ALERT: pin18
             The sensor alert pin is connected to a GPIO pin to check if the sensor is triggering 
             alerts. The pin is pulled to VCC via the board internal pull-up resistor.
             The pin is active low. Wire an external pull-up resistor to VCC if needed.

Prerequisites:
    - Install the unittest module in the MicroPython device.
    - Install the MCP9808 driver in the MicroPython device.
    - Wire the sensor to the board as described above.
    - Run the test suite.
"""

import unittest
import mcp9808
from mcp9808 import MCP9808
from machine import SoftI2C, Pin
from time import sleep_ms

##############################################
# Change the pin numbers to match your setup #
##############################################
power_pin = Pin(15, Pin.OUT)
alert_pin = Pin(18, Pin.IN, pull=Pin.PULL_UP)
i2c_bus = SoftI2C(scl=Pin(17), sda=Pin(16), freq=400000)


class TestMCP9808(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.power: Pin = power_pin
        cls.alert: Pin = alert_pin
        cls.i2c: SoftI2C = i2c_bus
        cls.sensor = MCP9808(cls.i2c)

    def setUp(self) -> None:
        self.power.off()
        sleep_ms(20)
        self.power.on()
        sleep_ms(2000)

    def test_powerup_defaults(self) -> None:
        self.assertEqual(self.sensor.hyst_mode, mcp9808.HYST_00)
        self.assertFalse(self.sensor.shdn)
        self.assertFalse(self.sensor.crit_lock)
        self.assertFalse(self.sensor.alerts_lock)
        self.assertFalse(self.sensor.irq_clear_bit)
        self.assertFalse(self.sensor.alert)
        self.assertFalse(self.sensor.alert_ctrl)
        self.assertFalse(self.sensor.alert_sel)
        self.assertFalse(self.sensor.alert_pol)
        self.assertFalse(self.sensor.alert_mode)

    def test_hysteresis_set(self) -> None:
        self.sensor.hyst_mode = mcp9808.HYST_15
        self.assertEqual(self.sensor.hyst_mode, mcp9808.HYST_15)
        self.sensor.hyst_mode = mcp9808.HYST_30
        self.assertEqual(self.sensor.hyst_mode, mcp9808.HYST_30)
        self.sensor.hyst_mode = mcp9808.HYST_60
        self.assertEqual(self.sensor.hyst_mode, mcp9808.HYST_60)
        self.sensor.hyst_mode = mcp9808.HYST_00
        self.assertEqual(self.sensor.hyst_mode, mcp9808.HYST_00)

    def test_shutdown(self) -> None:
        self.sensor.shutdown()
        self.assertTrue(self.sensor.shdn)
        self.sensor.wake()
        self.assertFalse(self.sensor.shdn)

    def test_crit_lock(self) -> None:
        # Lock critical limit register
        self.sensor.lock_crit_limit()
        # Check if the critical limit register is locked
        self.assertTrue(self.sensor.crit_lock)
        # Try to enable alerts
        self.sensor.enable_alert()
        # Alerts should not be enabled
        self.assertFalse(self.sensor.alert_ctrl)
        # Reset sensor
        self.setUp()
        # Check if the critical limit register is unlocked
        self.assertFalse(self.sensor.crit_lock)

    def test_alerts_lock(self) -> None:
        # Lock alerts limit registers
        self.sensor.lock_alerts_limit()
        # Check if the alerts limit registers are locked
        self.assertTrue(self.sensor.alerts_lock)
        # Try to enable alerts
        self.sensor.enable_alert()
        # Alerts should not be enabled
        self.assertTrue(self.sensor.alerts_lock)
        # Reset sensor
        self.setUp()
        # Check if the alerts limit registers are unlocked
        self.assertFalse(self.sensor.alerts_lock)

    def test_alert_control(self) -> None:
        # Get current temperature
        temp: float = self.sensor.get_temperature()
        # Enable alerts
        self.sensor.enable_alert()
        # Check if alerts are enabled
        self.assertTrue(self.sensor.alert_ctrl)
        # Set lower limit to current temperature + 10°C
        self.sensor.set_alert_lower_limit(temp + 10)
        sleep_ms(10)
        # Check if hardware alert is triggered
        self.assertEqual(self.alert.value(), 0)
        # Disable alerts
        self.sensor.disable_alert()
        # Check if alerts are disabled
        self.assertFalse(self.sensor.alert_ctrl)
        # Check if hardware alert is cleared
        self.assertEqual(self.alert.value(), 1)

    def test_comp_lower_alerts(self) -> None:
        # Get current temperature
        temp: float = self.sensor.get_temperature()
        # Check if alert is disabled and in comparator mode
        self.assertFalse(self.sensor.alert_ctrl)
        self.assertFalse(self.sensor.alert_mode)
        # Set upper limit to 100°C
        #     crit limit to 100°C
        #     lower limit to current temperature + 10°C
        self.sensor.set_alert_upper_limit(100)
        self.sensor.set_alert_crit_limit(100)
        self.sensor.set_alert_lower_limit(temp + 10)
        # Enable alerts
        self.sensor.enable_alert()
        sleep_ms(10)
        # Check if hardware alert is triggered
        self.assertEqual(self.alert.value(), 0)
        # Check if correct alert trigger bit is set
        self.assertEqual(self.sensor.get_alert_triggers(), (False, False, True))
        # Set lower limit to current temperature - 10°C (simulating temperature increase)
        self.sensor.set_alert_lower_limit(temp - 10)
        sleep_ms(10)
        # Check if hardware alert is cleared
        self.assertEqual(self.alert.value(), 1)
        # Check if correct alert trigger bit is cleared
        self.assertEqual(self.sensor.get_alert_triggers(), (False, False, False))

    def test_comp_upper_alerts(self) -> None:
        # Get current temperature
        temp: float = self.sensor.get_temperature()
        # Check if alert is disabled and in comparator mode
        self.assertFalse(self.sensor.alert_ctrl)
        self.assertFalse(self.sensor.alert_mode)
        # Set lower limit to 0°C
        #     crit limit to 100°C
        #     upper limit to current temperature - 10°C
        self.sensor.set_alert_lower_limit(0)
        self.sensor.set_alert_crit_limit(100)
        self.sensor.set_alert_upper_limit(temp - 10)
        # Enable alerts
        self.sensor.enable_alert()
        sleep_ms(10)
        # Check if hardware alert is triggered
        self.assertEqual(self.alert.value(), 0)
        # Check if correct alert trigger bit is set
        self.assertEqual(self.sensor.get_alert_triggers(), (False, True, False))
        # Set lower limit to current temperature + 10°C (simulating temperature drop)
        self.sensor.set_alert_upper_limit(temp + 10)
        sleep_ms(10)
        # Check if hardware alert is cleared
        self.assertEqual(self.alert.value(), 1)
        # Check if correct alert trigger bit is cleared
        self.assertEqual(self.sensor.get_alert_triggers(), (False, False, False))

    def test_comp_crit_alerts(self) -> None:
        # Get current temperature
        temp: float = self.sensor.get_temperature()
        # Check if alert is disabled and in comparator mode
        self.assertFalse(self.sensor.alert_ctrl)
        self.assertFalse(self.sensor.alert_mode)
        # Set lower limit to 0°C
        #     upper limit to 100°C
        #     crit limit to current temperature - 10°C
        self.sensor.set_alert_lower_limit(0)
        self.sensor.set_alert_upper_limit(100)
        self.sensor.set_alert_crit_limit(temp - 10)
        # Enable alerts
        self.sensor.enable_alert()
        sleep_ms(10)
        # Check if hardware alert is triggered
        self.assertEqual(self.alert.value(), 0)
        # Check if correct alert trigger bit is set
        self.assertEqual(self.sensor.get_alert_triggers(), (True, False, False))
        # Set lower limit to current temperature + 10°C (simulating temperature drop)
        self.sensor.set_alert_crit_limit(temp + 10)
        sleep_ms(10)
        # Check if hardware alert is cleared
        self.assertEqual(self.alert.value(), 1)
        # Check if correct alert trigger bit is cleared
        self.assertEqual(self.sensor.get_alert_triggers(), (False, False, False))

    def test_irq_lower_alerts(self) -> None:
        # Get current temperature
        temp: float = self.sensor.get_temperature()
        # Check if alert is disabled and in comparator mode
        self.assertFalse(self.sensor.alert_ctrl)
        self.assertFalse(self.sensor.alert_mode)
        # Set and check alert mode to IRQ
        self.sensor.set_alert_mode(irq=True)
        self.assertTrue(self.sensor.alert_mode)
        # Set lower limit to current temperature + 10°C
        #     upper limit to 100°C
        #     crit limit to 100°C
        self.sensor.set_alert_lower_limit(temp + 10)
        self.sensor.set_alert_upper_limit(100)
        self.sensor.set_alert_crit_limit(100)
        # Enable alerts
        self.sensor.enable_alert()
        sleep_ms(10)
        # Check if hardware IRQ is triggered
        self.assertEqual(self.alert.value(), 0)
        # Check if correct alert trigger bit is set
        self.assertEqual(self.sensor.get_alert_triggers(), (False, False, True))
        # Clear IRQ
        self.sensor.irq_clear()
        # Check if hardware IRQ is cleared
        self.assertEqual(self.alert.value(), 1)
        # Check if correct alert trigger bit is still set
        self.assertEqual(self.sensor.get_alert_triggers(), (False, False, True))
        # Set lower limit to current temperature - 10°C (simulating temperature increase)
        self.sensor.set_alert_lower_limit(temp - 10)
        sleep_ms(10)
        # Check if hardware IRQ is triggered
        self.assertEqual(self.alert.value(), 0)
        # Check if correct alert trigger bit is cleared
        self.assertEqual(self.sensor.get_alert_triggers(), (False, False, False))
        # Clear IRQ
        self.sensor.irq_clear()
        # Check if alert is cleared
        self.assertEqual(self.alert.value(), 1)
        # Check if correct alert trigger bit is cleared
        self.assertEqual(self.sensor.get_alert_triggers(), (False, False, False))

    def test_irq_upper_alerts(self) -> None:
        # Get current temperature
        temp: float = self.sensor.get_temperature()
        # Check if alert is disabled and in comparator mode
        self.assertFalse(self.sensor.alert_ctrl)
        self.assertFalse(self.sensor.alert_mode)
        # Set and check alert mode to IRQ
        self.sensor.set_alert_mode(irq=True)
        self.assertTrue(self.sensor.alert_mode)
        # Set lower limit 0°C
        #     upper limit to current temperature - 10°C
        #     crit limit to 100°C
        self.sensor.set_alert_lower_limit(0)
        self.sensor.set_alert_upper_limit(temp - 10)
        self.sensor.set_alert_crit_limit(100)
        # Enable alerts
        self.sensor.enable_alert()
        sleep_ms(10)
        # Check if hardware IRQ is triggered
        self.assertEqual(self.alert.value(), 0)
        # Check if correct alert trigger bit is set
        self.assertEqual(self.sensor.get_alert_triggers(), (False, True, False))
        # Clear IRQ
        self.sensor.irq_clear()
        # Check if hardware IRQ is cleared
        self.assertEqual(self.alert.value(), 1)
        # Check if correct alert trigger bit is still set
        self.assertEqual(self.sensor.get_alert_triggers(), (False, True, False))
        # Set upper limit to current temperature + 10°C (simulating temperature drop)
        self.sensor.set_alert_upper_limit(temp + 10)
        sleep_ms(10)
        # Check if hardware IRQ is triggered
        self.assertEqual(self.alert.value(), 0)
        # Check if correct alert trigger bit is cleared
        self.assertEqual(self.sensor.get_alert_triggers(), (False, False, False))
        # Clear IRQ
        self.sensor.irq_clear()
        # Check if alert is cleared
        self.assertEqual(self.alert.value(), 1)
        # Check if correct alert trigger bit is cleared
        self.assertEqual(self.sensor.get_alert_triggers(), (False, False, False))

    def test_irq_crit_alerts(self) -> None:
        # Get current temperature
        temp: float = self.sensor.get_temperature()
        # Check if alert is disabled and in comparator mode
        self.assertFalse(self.sensor.alert_ctrl)
        self.assertFalse(self.sensor.alert_mode)
        # Set and check alert mode to IRQ
        self.sensor.set_alert_mode(irq=True)
        self.assertTrue(self.sensor.alert_mode)
        # Set lower limit 0°C
        #     upper limit to current temperature - 10°C
        #     crit limit to 100°C
        self.sensor.set_alert_lower_limit(0)
        self.sensor.set_alert_upper_limit(temp - 10)
        self.sensor.set_alert_crit_limit(100)
        # Enable alerts (first IRQ from upper limit)
        self.sensor.enable_alert()
        sleep_ms(10)
        # Check if alert is triggered
        self.assertEqual(self.alert.value(), 0)
        # Check if correct alert trigger bit is set
        self.assertEqual(self.sensor.get_alert_triggers(), (False, True, False))
        # Clear IRQ
        self.sensor.irq_clear()
        # Check if alert is cleared
        self.assertEqual(self.alert.value(), 1)
        # Check if correct alert trigger bit is still set
        self.assertEqual(self.sensor.get_alert_triggers(), (False, True, False))
        # Set crit limit to current temperature - 5°C (to trigger second IRQ from crit limit)
        self.sensor.set_alert_crit_limit(temp - 5)
        sleep_ms(10)
        # Check if alert is triggered (second IRQ from crit limit)
        self.assertEqual(self.alert.value(), 0)
        # Check if correct alert trigger bit is set
        self.assertEqual(self.sensor.get_alert_triggers(), (True, True, False))
        # Clear IRQ
        self.sensor.irq_clear()
        # Check if alert is NOT cleard
        self.assertEqual(self.alert.value(), 0)
        # Check if correct alert trigger bit is still set
        self.assertEqual(self.sensor.get_alert_triggers(), (True, True, False))
        # Set crit limit to current temperature + 5°C (simulating temperature drop)
        self.sensor.set_alert_crit_limit(temp + 5)
        sleep_ms(10)
        # Check if alert is cleared
        self.assertEqual(self.alert.value(), 1)
        # Check if correct alert trigger bit is cleared
        self.assertEqual(self.sensor.get_alert_triggers(), (False, True, False))


if __name__ == "__main__":
    unittest.main()
