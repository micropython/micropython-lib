# Test advertising multiple services, and scanning them.

import sys

# ruff: noqa: E402
sys.path.append("")

import asyncio
import aioble
import bluetooth

TIMEOUT_MS = 5000

_SERVICE_16_A = bluetooth.UUID(0x180F)  # Battery Service
_SERVICE_16_B = bluetooth.UUID(0x181A)  # Environmental Sensing Service
_SERVICE_32_A = bluetooth.UUID("AB12")  # random
_SERVICE_32_B = bluetooth.UUID("CD34")  # random


# Acting in peripheral role (advertising).
async def instance0_task():
    multitest.globals(BDADDR=aioble.config("mac"))
    multitest.next()

    # Advertise, and wait for central to connect to us.
    print("advertise")
    async with await aioble.advertise(
        20_000,
        name="MPY",
        services=[_SERVICE_16_A, _SERVICE_16_B, _SERVICE_32_A, _SERVICE_32_B],
        timeout_ms=TIMEOUT_MS,
    ) as connection:
        print("connected")
        await connection.disconnected()
        print("disconnected")


def instance0():
    try:
        asyncio.run(instance0_task())
    finally:
        aioble.stop()


# Acting in central role (scanning).
async def instance1_task():
    multitest.next()

    wanted_device = aioble.Device(*BDADDR)

    # Scan for the wanted device/peripheral and print its advertised services.
    async with aioble.scan(5000, interval_us=30000, window_us=30000, active=True) as scanner:
        async for result in scanner:
            if result.device == wanted_device:
                services = list(result.services())
                if services:
                    print(services)
                    break

    # Connect to peripheral and then disconnect.
    print("connect")
    device = aioble.Device(*BDADDR)
    async with await device.connect(timeout_ms=TIMEOUT_MS):
        print("disconnect")


def instance1():
    try:
        asyncio.run(instance1_task())
    finally:
        aioble.stop()
