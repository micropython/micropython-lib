# Test characteristic read/write/notify from both GATTS and GATTC.

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
CHAR1_UUID = bluetooth.UUID("00000000-1111-2222-3333-444444444444")
CHAR2_UUID = bluetooth.UUID("00000000-1111-2222-3333-555555555555")
CHAR3_UUID = bluetooth.UUID("00000000-1111-2222-3333-666666666666")


# Acting in peripheral role.
async def instance0_task():
    service = aioble.Service(SERVICE_UUID)
    characteristic1 = aioble.BufferedCharacteristic(service, CHAR1_UUID, write=True)
    characteristic2 = aioble.BufferedCharacteristic(service, CHAR2_UUID, write=True, max_len=40)
    characteristic3 = aioble.BufferedCharacteristic(
        service, CHAR3_UUID, write=True, max_len=80, append=True
    )
    aioble.register_services(service)

    multitest.globals(BDADDR=aioble.config("mac"))
    multitest.next()

    # Wait for central to connect to us.
    print("advertise")
    connection = await aioble.advertise(
        20_000, adv_data=b"\x02\x01\x06\x04\xffMPY", timeout_ms=TIMEOUT_MS
    )
    print("connected")

    # The first will just see the second write (truncated).
    await characteristic1.written(timeout_ms=TIMEOUT_MS)
    await characteristic1.written(timeout_ms=TIMEOUT_MS)
    print("written", characteristic1.read())

    # The second will just see the second write (still truncated because MTU
    # exchange hasn't happened).
    await characteristic2.written(timeout_ms=TIMEOUT_MS)
    await characteristic2.written(timeout_ms=TIMEOUT_MS)
    print("written", characteristic2.read())

    # MTU exchange should happen here.

    # The second will now see the full second write.
    await characteristic2.written(timeout_ms=TIMEOUT_MS)
    await characteristic2.written(timeout_ms=TIMEOUT_MS)
    print("written", characteristic2.read())

    # The third will see the two full writes concatenated.
    await characteristic3.written(timeout_ms=TIMEOUT_MS)
    await characteristic3.written(timeout_ms=TIMEOUT_MS)
    print("written", characteristic3.read())

    # Wait for the central to disconnect.
    await connection.disconnected(timeout_ms=TIMEOUT_MS)
    print("disconnected")


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
    connection = await device.connect(timeout_ms=TIMEOUT_MS)

    # Discover characteristics.
    service = await connection.service(SERVICE_UUID)
    print("service", service.uuid)
    characteristic1 = await service.characteristic(CHAR1_UUID)
    print("characteristic1", characteristic1.uuid)
    characteristic2 = await service.characteristic(CHAR2_UUID)
    print("characteristic2", characteristic2.uuid)
    characteristic3 = await service.characteristic(CHAR3_UUID)
    print("characteristic3", characteristic3.uuid)

    # Write to each characteristic twice, with a long enough value to trigger
    # truncation.
    print("write1")
    await characteristic1.write(
        "central1-aaaaaaaaaaaaaaaaaaaaaaaaaaaaa", response=True, timeout_ms=TIMEOUT_MS
    )
    await characteristic1.write(
        "central1-bbbbbbbbbbbbbbbbbbbbbbbbbbbbb", response=True, timeout_ms=TIMEOUT_MS
    )
    print("write2a")
    await characteristic2.write(
        "central2a-aaaaaaaaaaaaaaaaaaaaaaaaaaaa", response=True, timeout_ms=TIMEOUT_MS
    )
    await characteristic2.write(
        "central2a-bbbbbbbbbbbbbbbbbbbbbbbbbbbb", response=True, timeout_ms=TIMEOUT_MS
    )
    print("exchange mtu")
    await connection.exchange_mtu(100)
    print("write2b")
    await characteristic2.write(
        "central2b-aaaaaaaaaaaaaaaaaaaaaaaaaaaa", response=True, timeout_ms=TIMEOUT_MS
    )
    await characteristic2.write(
        "central2b-bbbbbbbbbbbbbbbbbbbbbbbbbbbb", response=True, timeout_ms=TIMEOUT_MS
    )
    print("write3")
    await characteristic3.write(
        "central3-aaaaaaaaaaaaaaaaaaaaaaaaaaaaa", response=True, timeout_ms=TIMEOUT_MS
    )
    await characteristic3.write(
        "central3-bbbbbbbbbbbbbbbbbbbbbbbbbbbbb", response=True, timeout_ms=TIMEOUT_MS
    )

    # Disconnect from peripheral.
    print("disconnect")
    await connection.disconnect(timeout_ms=TIMEOUT_MS)
    print("disconnected")


def instance1():
    try:
        asyncio.run(instance1_task())
    finally:
        aioble.stop()
