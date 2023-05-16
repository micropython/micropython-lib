# Tests for PASCO2 module
from machine import I2C
import time
import pasco2 as sensor

i2c = I2C(0)
pasco2 = sensor.PASCO2(i2c)


def sensor_init():
    init_status = pasco2.initialize()
    return init_status


def sensor_get_specs():
    # read product id
    sensorID = pasco2.get_prod_id()
    # read revision id
    revID = pasco2.get_rev_id()
    return [sensorID, revID]


def sensor_get_values():
    co2ppm = pasco2.get_co2_value()
    return co2ppm


print("PASCO2 test module running")
print("\nTest 1: Sensor Init")
print("Status: Test", "passed" if sensor_init() == 0 else "failed")
print("\nTest 2: Get sensor specs")
specs = sensor_get_specs()
print("Status: Test", "passed" if (specs.count(-1) == 0) else "failed")
print("\nTest 3: Get sensor values for 100 cycles")
for i in range(0, 100):
    time.sleep(1)
    co2ppm = sensor_get_values()
    if co2ppm != -1:
        print(
            "Status: Test",
            "passed" if (co2ppm in range(0, 1000)) else "failed",
            "[CO2 Value:",
            co2ppm,
            "]",
        )
