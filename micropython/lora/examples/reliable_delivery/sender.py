# MicroPython lora reliable_delivery example - synchronous sender program
# MIT license; Copyright (c) 2023 Angus Gratton
import machine
from machine import SPI, Pin
import random
import struct
import time

from lora_rd_settings import RECEIVER_ID, ACK_LENGTH, ACK_DELAY_MS, lora_cfg

SLEEP_BETWEEN_MS = 5000  # Main loop should sleep this long between sending data to the receiver

MAX_RETRIES = 4  # Retry each message this often if no ACK is received

# Initial retry is after this long. Increases by 1.25x each subsequent retry.
BASE_RETRY_TIMEOUT_MS = 1000

# Add random jitter to each retry period, up to this long. Useful to prevent two
# devices ending up in sync.
RETRY_JITTER_MS = 1500

# If reported RSSI value is lower than this, increase
# output power 1dBm
RSSI_WEAK_THRESH = -110

# If reported RSSI value is higher than this, decrease
# output power 1dBm
RSSI_STRONG_THRESH = -70

# IMPORTANT: Set this to the maximum output power in dBm that is permitted in
# your regulatory environment.
OUTPUT_MAX_DBM = 15
OUTPUT_MIN_DBM = -20


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
    modem = get_modem()

    # Unique ID of this sender, 16-bit number. This method of generating an ID is pretty crummy,
    # if using this in a real application then probably better to store these in the filesystem or
    # something like that
    DEVICE_ID = sum(b for b in machine.unique_id()) & 0xFFFF

    sender = Sender(modem, DEVICE_ID)
    while True:
        sensor_data = get_sensor_data()
        sender.send(sensor_data)

        # Sleep until the next time we should read the sensor data and send it to
        # the receiver.
        #
        # The goal for the device firmware is to spend most of its time in the lowest
        # available sleep state, to save power.
        #
        # Note that if the sensor(s) in a real program generates events, these can be
        # hooked to interrupts and used to wake Micropython up to send data,
        # instead.
        modem.sleep()
        time.sleep_ms(SLEEP_BETWEEN_MS)  # TODO see if this can be machine.lightsleep()


def get_sensor_data():
    # Return a bytes object with the latest sensor data to send to the receiver.
    #
    # As this is just an example, we send a dummy payload which is just a string
    # containing our ticks_ms() timestamp.
    #
    # In a real application the sensor data should usually be binary data and
    # not a string, to save transmission size.
    return f"Hello, ticks_ms={time.ticks_ms()}".encode()


class Sender:
    def __init__(self, modem, device_id):
        self.modem = modem
        self.device_id = device_id
        self.counter = 0
        self.output_power = lora_cfg["output_power"]  # start with common settings power level
        self.rx_ack = None  # reuse the ack message object when we can

        print(f"Sender initialized with ID {device_id:#x}")
        random.seed(device_id)
        self.adjust_output_power(0)  # set the initial value within MIN/MAX

        modem.calibrate()

    def send(self, sensor_data, adjust_output_power=True):
        # Send a packet of sensor data to the receiver reliably.
        #
        # Returns True if data was successfully sent and ACKed, False otherwise.
        #
        # If adjust_output_power==True then increase or decrease output power
        # according to the RSSI reported in the ACK packet.
        self.counter = (self.counter + 1) & 0xFF

        # Prepare the simple payload with header and checksum
        # See README for a summary of the simple data message format
        payload = bytearray(len(sensor_data) + 5)
        struct.pack_into("<HBB", payload, 0, self.device_id, self.counter, len(sensor_data))
        payload[4:-1] = sensor_data
        payload[-1] = sum(b for b in payload) & 0xFF

        # Calculate the time on air (in milliseconds) for an ACK packet
        ack_packet_ms = self.modem.get_time_on_air_us(ACK_LENGTH) // 1000 + 1
        timeout = BASE_RETRY_TIMEOUT_MS

        print(f"Sending {len(payload)} bytes")

        # Send the payload, until we receive an acknowledgement or run out of retries
        for _ in range(MAX_RETRIES):
            # Using simple API here.
            #
            # We could reduce power consumption a little by going to sleep
            # instead of waiting for the send/recv to complete, but doing
            # this well involves setting port-specific wakeup settings. Provided
            # "dio" pin is assigned then the MCU will mostly be in a lower power
            # idle state while the radio sends, at least.
            sent_at = self.modem.send(payload)

            # We expect the receiver of a valid message to start sending the ACK
            # approximately ACK_DELAY_MS after receiving the message (to allow
            # the sender time to reconfigure the modem.)
            #
            # We start receiving as soon as we can, but allow up to
            # ACK_DELAY_MS*2 of total timing leeway - plus the time on air for
            # the message itself
            maybe_ack = self.modem.recv(ack_packet_ms + ACK_DELAY_MS * 2, rx_packet=self.rx_ack)

            # Check if the packet we received is a valid ACK
            rssi = self._ack_is_valid(maybe_ack, payload[-1])

            if rssi is not None:  # ACK is valid
                self.rx_ack == maybe_ack

                delta = time.ticks_diff(maybe_ack.ticks_ms, sent_at)
                print(
                    f"ACKed with RSSI {rssi}, {delta}ms after sent "
                    + f"(skew {delta-ACK_DELAY_MS-ack_packet_ms}ms)"
                )

                if adjust_output_power:
                    if rssi > RSSI_STRONG_THRESH:
                        self.adjust_output_power(-1)
                    elif rssi < RSSI_WEAK_THRESH:
                        self.adjust_output_power(1)

                return True

            # Otherwise, prepare to sleep briefly and then retry
            next_try_at = time.ticks_add(sent_at, timeout)
            sleep_time = time.ticks_diff(next_try_at, time.ticks_ms()) + random.randrange(
                RETRY_JITTER_MS
            )
            if sleep_time > 0:
                self.modem.sleep()
                time.sleep_ms(sleep_time)  # TODO: see if this can be machine.lightsleep

            # add 25% timeout for next iteration
            timeout = (timeout * 5) // 4

        print(f"Failed, no ACK after {MAX_RETRIES} retries.")
        if adjust_output_power:
            self.adjust_output_power(2)
        self.modem.calibrate_image()  # try and improve the RX sensitivity for next time
        return False

    def _ack_is_valid(self, maybe_ack, csum):
        # Private function to verify if the RxPacket held in 'maybe_ack' is a valid ACK for the
        # current device_id and counter value, and provided csum value.
        #
        # If it is, returns the reported RSSI value from the packet.
        # If not, returns None
        if (not maybe_ack) or len(maybe_ack) != ACK_LENGTH:
            return None

        base_id, ack_id, ack_counter, ack_csum, rssi = struct.unpack("<HHBBb", maybe_ack)

        if (
            base_id != RECEIVER_ID
            or ack_id != self.device_id
            or ack_counter != self.counter
            or ack_csum != csum
        ):
            return None

        return rssi

    def adjust_output_power(self, delta_dbm):
        # Adjust the modem output power by +/-delta_dbm, max of OUTPUT_MAX_DBM
        #
        # (note: the radio may also apply its own power limit internally.)
        new = max(min(self.output_power + delta_dbm, OUTPUT_MAX_DBM), OUTPUT_MIN_DBM)
        self.output_power = new
        print(f"New output_power {new}/{OUTPUT_MAX_DBM} (delta {delta_dbm})")
        self.modem.configure({"output_power": self.output_power})


if __name__ == "__main__":
    main()
