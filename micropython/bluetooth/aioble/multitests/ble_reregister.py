# Test that singleton service/characteristic instances can be re-registered
# across multiple stop/start cycles without data loss.

import sys

# ruff: noqa: E402
sys.path.append("")

from micropython import const
import machine
import time

import asyncio
import aioble
import bluetooth

TIMEOUT_MS = 5000

SERVICE_UUID = bluetooth.UUID("A5A5A5A5-FFFF-9999-1111-5A5A5A5A5A5A")
CHAR_INITIAL_UUID = bluetooth.UUID("00000000-1111-2222-3333-444444444444")
CHAR_WRITE_UUID = bluetooth.UUID("00000000-1111-2222-3333-555555555555")


# Acting in peripheral role.
async def instance0_task():
    # Create service and characteristics ONCE (singleton pattern).
    service = aioble.Service(SERVICE_UUID)
    aioble.Characteristic(service, CHAR_INITIAL_UUID, read=True, initial=b"hello")
    char_write = aioble.Characteristic(service, CHAR_WRITE_UUID, read=True, write=True)

    multitest.globals(BDADDR=aioble.config("mac"))
    multitest.next()

    for i in range(3):
        # Re-register the same service instances.
        aioble.register_services(service)

        # Write a cycle-specific value to the writable characteristic.
        char_write.write("periph{}".format(i))

        multitest.broadcast("connect-{}".format(i))

        # Wait for central to connect.
        print("advertise", i)
        connection = await aioble.advertise(
            20_000, adv_data=b"\x02\x01\x06\x04\xffMPY", timeout_ms=TIMEOUT_MS
        )
        print("connected", i)

        # Wait for the central to write.
        await char_write.written(timeout_ms=TIMEOUT_MS)
        print("written", i)

        # Wait for the central to disconnect.
        await connection.disconnected(timeout_ms=TIMEOUT_MS)
        print("disconnected", i)

        # Shutdown aioble.
        print("shutdown", i)
        aioble.stop()

        await asyncio.sleep_ms(100)


def instance0():
    try:
        asyncio.run(instance0_task())
    finally:
        aioble.stop()


# Acting in central role.
async def instance1_task():
    multitest.next()

    for i in range(3):
        multitest.wait("connect-{}".format(i))

        # Connect to peripheral.
        print("connect", i)
        device = aioble.Device(*BDADDR)
        connection = await device.connect(timeout_ms=TIMEOUT_MS)

        # Discover characteristics.
        service = await connection.service(SERVICE_UUID)
        char_initial = await service.characteristic(CHAR_INITIAL_UUID)
        char_write = await service.characteristic(CHAR_WRITE_UUID)

        # Read the initial= characteristic — must be the same every cycle.
        print("read initial", await char_initial.read(timeout_ms=TIMEOUT_MS))

        # Read the writable characteristic — should have cycle-specific value.
        print("read written", await char_write.read(timeout_ms=TIMEOUT_MS))

        # Write to the writable characteristic.
        print("write", i)
        await char_write.write("central{}".format(i), response=True, timeout_ms=TIMEOUT_MS)

        # Disconnect from peripheral.
        print("disconnect", i)
        await connection.disconnect(timeout_ms=TIMEOUT_MS)
        print("disconnected", i)

        # Shutdown aioble.
        aioble.stop()

        await asyncio.sleep_ms(100)


def instance1():
    try:
        asyncio.run(instance1_task())
    finally:
        aioble.stop()
