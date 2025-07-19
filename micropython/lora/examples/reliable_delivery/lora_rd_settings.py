# MicroPython lora reliable_delivery example - common protocol settings
# MIT license; Copyright (c) 2023 Angus Gratton

#
######
# To be able to be able to communicate, most of these settings need to match on both radios.
# Consult the example README for more information about how to use the example.
######

# LoRa protocol configuration
#
# Currently configured for relatively slow & low bandwidth settings, which
# gives more link budget and possible range.
#
# These settings should match on receiver.
#
# Check the README and local regulations to know what configuration settings
# are available.
lora_cfg = {
    "freq_khz": 916000,
    "sf": 10,
    "bw": "62.5",  # kHz
    "coding_rate": 8,
    "preamble_len": 12,
    "output_power": 10,  # dBm
}

# Single receiver has a fixed 16-bit ID value (senders each have a unique value).
RECEIVER_ID = 0xFFFF

# Length of an ACK message in bytes.
ACK_LENGTH = 7

# Send the ACK this many milliseconds after receiving a valid message
#
# This can be quite a bit lower (25ms or so) if wakeup times are short
# and _DEBUG is turned off on the modems (logging to UART delays everything).
ACK_DELAY_MS = 100
