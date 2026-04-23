# Test BLE GAP pairing and bonding with aioble

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
CHAR_UUID = bluetooth.UUID("00000000-1111-2222-3333-444444444444")

_FLAG_READ = const(0x0002)
_FLAG_READ_ENCRYPTED = const(0x0200)


# For aioble, we need to directly use the low-level bluetooth API for encrypted characteristics
class EncryptedCharacteristic(aioble.Characteristic):
    def __init__(self, service, uuid, **kwargs):
        super().__init__(service, uuid, read=True, **kwargs)
        # Override flags to add encryption requirement
        self.flags |= _FLAG_READ_ENCRYPTED


# Acting in peripheral role.
async def instance0_task():
    # Clear any existing bond state
    import os

    try:
        os.remove("ble_secrets.json")
    except:
        pass

    service = aioble.Service(SERVICE_UUID)
    characteristic = EncryptedCharacteristic(service, CHAR_UUID)
    aioble.register_services(service)

    multitest.globals(BDADDR=aioble.config("mac"))
    multitest.next()

    # Write initial characteristic value.
    characteristic.write("encrypted_data")

    # Wait for central to connect to us.
    print("advertise")
    connection = await aioble.advertise(
        20_000, adv_data=b"\x02\x01\x06\x04\xffMPY", timeout_ms=TIMEOUT_MS
    )
    print("connected")

    # Wait for pairing to complete
    print("wait_for_pairing")
    start_time = time.ticks_ms()
    while not connection.encrypted and time.ticks_diff(time.ticks_ms(), start_time) < TIMEOUT_MS:
        await asyncio.sleep_ms(100)

    # Give a small delay for bonding state to stabilize
    await asyncio.sleep_ms(200)

    if connection.encrypted:
        print(
            "paired encrypted=1 authenticated={} bonded={}".format(
                1 if connection.authenticated else 0, 1 if connection.bonded else 0
            )
        )
    else:
        print("pairing_timeout")

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

    # Clear any existing bond state
    import os

    try:
        os.remove("ble_secrets.json")
    except:
        pass

    # Connect to peripheral.
    print("connect")
    device = aioble.Device(*BDADDR)
    connection = await device.connect(timeout_ms=TIMEOUT_MS)

    # Discover characteristics (before pairing).
    service = await connection.service(SERVICE_UUID)
    print("service", service.uuid)
    characteristic = await service.characteristic(CHAR_UUID)
    print("characteristic", characteristic.uuid)

    # Pair with the peripheral.
    print("pair")
    await connection.pair(
        bond=False,  # Don't bond for this test
        le_secure=True,
        mitm=False,
        timeout_ms=TIMEOUT_MS,
    )

    # Give a small delay for bonding state to stabilize
    await asyncio.sleep_ms(200)

    print(
        "paired encrypted={} authenticated={} bonded={}".format(
            1 if connection.encrypted else 0,
            1 if connection.authenticated else 0,
            1 if connection.bonded else 0,
        )
    )

    # Read the peripheral's characteristic, should be encrypted.
    print("read_encrypted")
    data = await characteristic.read(timeout_ms=TIMEOUT_MS)
    print("read", data)

    # Disconnect from peripheral.
    print("disconnect")
    await connection.disconnect(timeout_ms=TIMEOUT_MS)
    print("disconnected")


def instance1():
    try:
        asyncio.run(instance1_task())
    finally:
        aioble.stop()
