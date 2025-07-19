# MicroPython lora reliable_delivery example - asynchronous receiver program
# MIT license; Copyright (c) 2023 Angus Gratton
import struct
import time
import asyncio
from machine import SPI, Pin
from micropython import const

from lora_rd_settings import RECEIVER_ID, ACK_LENGTH, ACK_DELAY_MS, lora_cfg

# Change _DEBUG to const(True) to get some additional debugging output
# about timing, RSSI, etc.
#
# For a lot more debugging detail, go to the modem driver and set _DEBUG there to const(True)
_DEBUG = const(False)

# Keep track of the last counter value we got from each known sender
# this allows us to tell if packets are being lost
last_counters = {}


def get_async_modem():
    # from lora import AsyncSX1276
    # return AsyncSX1276(
    #     spi=SPI(1, baudrate=2000_000, polarity=0, phase=0,
    #             miso=Pin(19), mosi=Pin(27), sck=Pin(5)),
    #     cs=Pin(18),
    #     dio0=Pin(26),
    #     dio1=Pin(35),
    #     reset=Pin(14),
    #     lora_cfg=lora_cfg,
    # )
    raise NotImplementedError("Replace this function with one that returns a lora modem instance")


def main():
    # Initializing the modem.
    #

    print("Initializing...")
    modem = get_async_modem()
    asyncio.run(recv_continuous(modem, rx_callback))


async def rx_callback(sender_id, data):
    # Do something with the data!
    print(f"Received {data} from {sender_id:#x}")


async def recv_continuous(modem, callback):
    # Async task which receives packets from the AsyncModem recv_continuous()
    # iterator, checks if they are valid, and send back an ACK if needed.
    #
    # On each successful message, we await callback() to allow the application
    # to do something with the data. Callback args are sender_id (as int) and the bytes
    # of the message payload.

    last_counters = {}  # Track the last counter value we got from each sender ID
    ack_buffer = bytearray(ACK_LENGTH)  # reuse the same buffer for ACK packets
    skipped_packets = 0  # Counter of skipped packets

    modem.calibrate()

    async for rx in modem.recv_continuous():
        # Filter 'rx' packet to determine if it's valid for our application
        if len(rx) < 5:  # 4 byte header plus 1 byte checksum
            print("Invalid packet length")
            continue

        sender_id, counter, data_len = struct.unpack("<HBB", rx)
        csum = rx[-1]

        if len(rx) != data_len + 5:
            print("Invalid length in payload header")
            continue

        calc_csum = sum(b for b in rx[:-1]) & 0xFF
        if csum != calc_csum:
            print(f"Invalid checksum. calc={calc_csum:#x} received={csum:#x}")
            continue

        # Packet is valid!

        if _DEBUG:
            print(f"RX {data_len} byte message RSSI {rx.rssi} at timestamp {rx.ticks_ms}")

        # Send the ACK
        struct.pack_into("<HHBBb", ack_buffer, 0, RECEIVER_ID, sender_id, counter, csum, rx.rssi)

        # Time send to start as close to ACK_DELAY_MS after message was received as possible
        tx_at_ms = time.ticks_add(rx.ticks_ms, ACK_DELAY_MS)
        tx_done = await modem.send(ack_buffer, tx_at_ms=tx_at_ms)

        if _DEBUG:
            tx_time = time.ticks_diff(tx_done, tx_at_ms)
            expected = modem.get_time_on_air_us(ACK_LENGTH) / 1000
            print(f"ACK TX {tx_at_ms}ms -> {tx_done}ms took {tx_time}ms expected {expected}")

        # Check if the data we received is fresh or stale
        if sender_id not in last_counters:
            print(f"New device id {sender_id:#x}")
        elif last_counters[sender_id] == counter:
            print(f"Duplicate packet received from {sender_id:#x}")
            continue
        elif counter != 1:
            # If the counter from this sender has gone up by more than 1 since
            # last time we got a packet, we know there is some packet loss.
            #
            # (ignore the case where the new counter is 1, as this probably
            # means a reset.)
            delta = (counter - 1 - last_counters[sender_id]) & 0xFF
            if delta:
                print(f"Skipped/lost {delta} packets from {sender_id:#x}")
                skipped_packets += delta

        last_counters[sender_id] = counter
        await callback(sender_id, rx[4:-1])


if __name__ == "__main__":
    main()
