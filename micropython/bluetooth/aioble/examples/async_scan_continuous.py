'''
Author : LakshmiNarasimman Ravichandran
email  : sriram@radiostudio.biz
File   : Sample gap_scanner based on aioble library

Description:
This will continuously scan for nearby advertisements and will print the scanned response,
if the local name and the service UUID matches the user data service ID 0x181C. 

Also will print the data advertised on Manufacturer data field with Characteristic ID: 0X2A06 - Alert Level

Can be terminated with Keyboard interrupt on REPL console

Tested MicroPython Observer Platform: esp32
Broadcaster Platform: nRF Connect Mobile App
'''

import sys
sys.path.append("")
from micropython import const
import uasyncio as asyncio
import aioble
import bluetooth

import random
import struct
'''
uuid: 0x181C
name: User Data
id: org.bluetooth.service.user_data
'''
# org.bluetooth.service.UserData
_USER_CUSTOM_UUID = bluetooth.UUID(0x181C)
# Alert State Characteristic
'''
uuid: 0x2A06
name: Alert Level
id: org.bluetooth.characteristic.alert_level
desc: expected manufacturer id
'''
# org.bluetooth.characteristic.AlertLevel
_USER_ALERT_LEVEL_UUID = bluetooth.UUID(0x2A06)

# Perform a continuous scan
_SCAN_DURATION_MS = const(0)


async def find_adv():
    # Scan infinitely, in active mode, with very low interval/window (to
    # maximise detection rate).
    async with aioble.scan(_SCAN_DURATION_MS, interval_us=30000, window_us=30000, active=True) as scanner:
        async for result in scanner:
            # See if it matches our name and the expected service.
            if result.name() == "userdata" and _USER_CUSTOM_UUID in result.services():
                print("Device: {}, Address: {}, Services: {}".format(result.name(), result.device.addr_hex(), *result.services()))
                for mfg_id, mfg_data in result.manufacturer():
                    print("Manufacturer Id : {}, Manufacturer Data: {}".format(mfg_id,ord(mfg_data)))
                return result.device
            else:
                return None

# Main Function definition
async def main():
    while True:
        device = await find_adv()
        if device:
            print("Device: ",device)
        await asyncio.sleep_ms(0)

try:
    # Run the main function
    asyncio.run(main())
except KeyboardInterrupt as err:
    # Gracefully stop the aioble service during KeyboardInterrupt
    aioble.stop()
    print('Aborted by User')
