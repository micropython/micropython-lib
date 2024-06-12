# Test characteristic write capture preserves order across characteristics.

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

# Without the write ordering (via the shared queue) in server.py, this test
# passes with delay of 1, fails some at 5, fails more at 50
DUMMY_DELAY = 50

SERVICE_UUID = bluetooth.UUID("A5A5A5A5-FFFF-9999-1111-5A5A5A5A5A5A")
CHAR_FIRST_UUID = bluetooth.UUID("00000000-1111-2222-3333-444444444444")
CHAR_SECOND_UUID = bluetooth.UUID("00000000-1111-2222-3333-555555555555")


# Acting in peripheral role.
async def instance0_task():
    service = aioble.Service(SERVICE_UUID)
    characteristic_first = aioble.Characteristic(
        service,
        CHAR_FIRST_UUID,
        write=True,
        capture=True,
    )
    # Second characteristic enabled write capture.
    characteristic_second = aioble.Characteristic(
        service,
        CHAR_SECOND_UUID,
        write=True,
        capture=True,
    )
    aioble.register_services(service)

    # Register characteristic.written() handlers as asyncio background tasks.
    # The order of these is important!
    task_second = asyncio.create_task(task_written(characteristic_second, "second"))
    task_first = asyncio.create_task(task_written(characteristic_first, "first"))

    # This dummy task simulates background processing on a real system that
    # can block the asyncio loop for brief periods of time
    task_dummy_ = asyncio.create_task(task_dummy())

    multitest.globals(BDADDR=aioble.config("mac"))
    multitest.next()

    # Wait for central to connect to us.
    print("advertise")
    async with await aioble.advertise(
        20_000, adv_data=b"\x02\x01\x06\x04\xffMPY", timeout_ms=TIMEOUT_MS
    ) as connection:
        print("connected")

        await connection.disconnected()

    task_second.cancel()
    task_first.cancel()
    task_dummy_.cancel()


async def task_written(chr, label):
    while True:
        await chr.written()
        data = chr.read().decode()
        print(f"written: {label} {data}")


async def task_dummy():
    while True:
        time.sleep_ms(DUMMY_DELAY)
        await asyncio.sleep_ms(5)


def instance0():
    try:
        asyncio.run(instance0_task())
    finally:
        aioble.stop()


# Acting in central role.
async def instance1_task():
    multitest.next()

    # Connect to peripheral and then disconnect.
    print("connect")
    device = aioble.Device(*BDADDR)
    async with await device.connect(timeout_ms=TIMEOUT_MS) as connection:
        # Discover characteristics.
        service = await connection.service(SERVICE_UUID)
        print("service", service.uuid)
        characteristic_first = await service.characteristic(CHAR_FIRST_UUID)
        characteristic_second = await service.characteristic(CHAR_SECOND_UUID)
        print("characteristic", characteristic_first.uuid, characteristic_second.uuid)

        for i in range(5):
            print(f"write c{i}")
            await characteristic_first.write("c" + str(i), timeout_ms=TIMEOUT_MS)
            await characteristic_second.write("c" + str(i), timeout_ms=TIMEOUT_MS)

            await asyncio.sleep_ms(300)

        for i in range(5):
            print(f"write r{i}")
            await characteristic_second.write("r" + str(i), timeout_ms=TIMEOUT_MS)
            await characteristic_first.write("r" + str(i), timeout_ms=TIMEOUT_MS)

            await asyncio.sleep_ms(300)


def instance1():
    try:
        asyncio.run(instance1_task())
    finally:
        aioble.stop()
