# MicroPython lora reliable_delivery example - synchronous receiver program
# MIT license; Copyright (c) 2023 Angus Gratton
import struct
import time
import machine
from machine import SPI, Pin
from micropython import const
from lora import RxPacket

from lora_rd_settings import RECEIVER_ID, ACK_LENGTH, ACK_DELAY_MS, lora_cfg

# Change _DEBUG to const(True) to get some additional debugging output
# about timing, RSSI, etc.
#
# For a lot more debugging detail, go to the modem driver and set _DEBUG there to const(True)
_DEBUG = const(False)

# Keep track of the last counter value we got from each known sender
# this allows us to tell if packets are being lost
last_counters = {}


def get_modem():
    # from lora import SX1276
    # return SX1276(
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
    print("Initializing...")
    modem = get_modem()

    print("Main loop started")
    receiver = Receiver(modem)

    while True:
        # With wait=True, this function blocks until something is received and always
        # returns non-None
        sender_id, data = receiver.recv(wait=True)

        # Do something with the data!
        print(f"Received {data} from {sender_id:#x}")


class Receiver:
    def __init__(self, modem):
        self.modem = modem
        self.last_counters = {}  # Track the last counter value we got from each sender ID
        self.rx_packet = None  # Reuse RxPacket object when possible, save allocation
        self.ack_buffer = bytearray(ACK_LENGTH)  # reuse the same buffer for ACK packets
        self.skipped_packets = 0  # Counter of skipped packets

        modem.calibrate()

        # Start receiving immediately. We expect the modem to receive continuously
        self.will_irq = modem.start_recv(continuous=True)
        print("Modem initialized and started receive...")

    def recv(self, wait=True):
        # Receive a packet from the sender, including sending an ACK.
        #
        # Returns a tuple of the 16-bit sender id and the sensor data payload.
        #
        # This function should be called very frequently from the main loop (at
        # least every ACK_DELAY_MS milliseconds), to avoid not sending ACKs in time.
        #
        # If 'wait' argument is True (default), the function blocks indefinitely
        # until a packet is received. If False then it will return None
        # if no packet is available.
        #
        # Note that because we called start_recv(continuous=True), the modem
        # will keep receiving on its own - even if when we call send() to
        # send an ACK.
        while True:
            rx = self.modem.poll_recv(rx_packet=self.rx_packet)

            if isinstance(rx, RxPacket):  # value will be True or an RxPacket instance
                decoded = self._handle_rx(rx)
                if decoded:
                    return decoded  # valid LoRa packet and valid for this application

            if not wait:
                return None

            # Otherwise, wait for an IRQ (or have a short sleep) and then poll recv again
            # (receiver is not a low power node, so don't bother with sleep modes.)
            if self.will_irq:
                while not self.modem.irq_triggered():
                    machine.idle()
            else:
                time.sleep_ms(1)

    def _handle_rx(self, rx):
        # Internal function to handle a received packet and either send an ACK
        # and return the sender and the payload, or return None if packet
        # payload is invalid or a duplicate.

        if len(rx) < 5:  # 4 byte header plus 1 byte checksum
            print("Invalid packet length")
            return None

        sender_id, counter, data_len = struct.unpack("<HBB", rx)
        csum = rx[-1]

        if len(rx) != data_len + 5:
            print("Invalid length in payload header")
            return None

        calc_csum = sum(b for b in rx[:-1]) & 0xFF
        if csum != calc_csum:
            print(f"Invalid checksum. calc={calc_csum:#x} received={csum:#x}")
            return None

        # Packet is valid!

        if _DEBUG:
            print(f"RX {data_len} byte message RSSI {rx.rssi} at timestamp {rx.ticks_ms}")

        # Send the ACK
        struct.pack_into(
            "<HHBBb", self.ack_buffer, 0, RECEIVER_ID, sender_id, counter, csum, rx.rssi
        )

        # Time send to start as close to ACK_DELAY_MS after message was received as possible
        tx_at_ms = time.ticks_add(rx.ticks_ms, ACK_DELAY_MS)
        tx_done = self.modem.send(self.ack_buffer, tx_at_ms=tx_at_ms)

        if _DEBUG:
            tx_time = time.ticks_diff(tx_done, tx_at_ms)
            expected = self.modem.get_time_on_air_us(ACK_LENGTH) / 1000
            print(f"ACK TX {tx_at_ms}ms -> {tx_done}ms took {tx_time}ms expected {expected}")

        # Check if the data we received is fresh or stale
        if sender_id not in self.last_counters:
            print(f"New device id {sender_id:#x}")
        elif self.last_counters[sender_id] == counter:
            print(f"Duplicate packet received from {sender_id:#x}")
            return None
        elif counter != 1:
            # If the counter from this sender has gone up by more than 1 since
            # last time we got a packet, we know there is some packet loss.
            #
            # (ignore the case where the new counter is 1, as this probably
            # means a reset.)
            delta = (counter - 1 - self.last_counters[sender_id]) & 0xFF
            if delta:
                print(f"Skipped/lost {delta} packets from {sender_id:#x}")
                self.skipped_packets += delta

        self.last_counters[sender_id] = counter
        return sender_id, rx[4:-1]


if __name__ == "__main__":
    main()
