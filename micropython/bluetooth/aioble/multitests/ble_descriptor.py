# Test descriptor discovery/read/write from both GATTS and GATTC.

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
CHAR1_DESC1_UUID = bluetooth.UUID("00000000-1111-2222-3333-444444444445")
CHAR1_DESC2_UUID = bluetooth.UUID("00000000-1111-2222-3333-444444444446")
CHAR2_UUID = bluetooth.UUID("00000000-1111-2222-3333-555555555555")
CHAR3_UUID = bluetooth.UUID("00000000-1111-2222-3333-666666666666")
CHAR3_DESC1_UUID = bluetooth.UUID("00000000-1111-2222-3333-666666666667")


# Acting in peripheral role.
async def instance0_task():
    service = aioble.Service(SERVICE_UUID)
    char1 = aioble.Characteristic(
        service, CHAR1_UUID, read=True, write=True, notify=True, indicate=True
    )
    char1_desc1 = aioble.Descriptor(char1, CHAR1_DESC1_UUID, read=True)
    char1_desc1.write("char1_desc1")
    char1_desc2 = aioble.Descriptor(char1, CHAR1_DESC2_UUID, read=True, write=True)
    char1_desc2.write("char1_desc2")
    aioble.Characteristic(service, CHAR2_UUID, read=True, write=True, notify=True, indicate=True)
    char3 = aioble.Characteristic(
        service, CHAR3_UUID, read=True, write=True, notify=True, indicate=True
    )
    char3_desc1 = aioble.Descriptor(char3, CHAR3_DESC1_UUID, read=True)
    char3_desc1.write("char3_desc1")
    aioble.register_services(service)

    multitest.globals(BDADDR=aioble.config("mac"))
    multitest.next()

    # Wait for central to connect to us.
    print("advertise")
    connection = await aioble.advertise(
        20_000, adv_data=b"\x02\x01\x06\x04\xffMPY", timeout_ms=TIMEOUT_MS
    )
    print("connected")

    await char1_desc2.written()
    print("written", char1_desc2.read())

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

    service = await connection.service(SERVICE_UUID)
    print("service", service.uuid)

    # Discover characteristics.
    uuids = []
    async for char in service.characteristics():
        uuids.append(char.uuid)
    print("found", sorted(uuids))

    char1 = await service.characteristic(CHAR1_UUID)
    print("char1", char1.uuid)

    uuids = []
    async for desc in char1.descriptors():
        uuids.append(desc.uuid)
    print("char1 descs", sorted(uuids))

    char1_desc1 = await char1.descriptor(CHAR1_DESC1_UUID)
    print("char1 desc1", char1_desc1.uuid)
    print("read", await char1_desc1.read())

    char1_desc2 = await char1.descriptor(CHAR1_DESC2_UUID)
    print("char1 desc2", char1_desc2.uuid)
    print("read", await char1_desc2.read())
    print("write")
    await char1_desc2.write("update")

    char2 = await service.characteristic(CHAR2_UUID)
    print("char2", char2.uuid)

    uuids = []
    async for desc in char2.descriptors():
        uuids.append(desc.uuid)
    print("char2 descs", sorted(uuids))

    char3 = await service.characteristic(CHAR3_UUID)
    print("char3", char3.uuid)

    uuids = []
    async for desc in char3.descriptors():
        uuids.append(desc.uuid)
    print("char3 descs", sorted(uuids))

    char3_desc1 = await char3.descriptor(CHAR3_DESC1_UUID)
    print("char3 desc1", char3_desc1.uuid)
    print("read", await char3_desc1.read())

    # Disconnect from peripheral.
    print("disconnect")
    await connection.disconnect(timeout_ms=TIMEOUT_MS)
    print("disconnected")


def instance1():
    try:
        asyncio.run(instance1_task())
    finally:
        aioble.stop()
