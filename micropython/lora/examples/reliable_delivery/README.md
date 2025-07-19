# LoRa Reliable Delivery Example

This example shows a basic custom protocol for reliable one way communication
from low-power remote devices to a central base device:

- A single "receiver" device, running on mains power, listens continuously for
  messages from one or more "sender" devices. Messages are payloads inside LoRa packets,
  with some additional framing and address in the LoRa packet payload.
- "Sender" devices are remote sensor nodes, possibly battery powered. These wake
  up periodically, read some data from a sensor, and send it in a message to the receiver.
- Messages are transmitted "reliably" with some custom header information,
  meaning the receiver will acknowledge it received each message and the sender
  will retry sending if it doesn't receive the acknowledgement.

## Source Files

* `lora_rd_settings.py` contains some common settings that are imported by
  sender and receiver. These settings will need to be modified for the correct
  frequency and other settings, before running the examples.
* `receiver.py` and `receiver_async.py` contain a synchronous (low-level API)
  and asynchronous (iterator API) implementation of the same receiver program,
  respectively. These two programs should work the same, they are intended show
  different ways the driver can be used.
* `sender.py` and `sender_async.py` contain a synchronous (simple API) and
  asynchronous (async API) implementation of the same sender program,
  respectively. Because the standard async API resembles the Simple API, these
  implementations are *very* similar. The two programs should work the same,
  they are intended to show different ways the driver can be used.

## Running the examples

One way to run this example interactively:

1. Install or "freeze in" the necessary lora modem driver package (`lora-sx127x`
   or `lora-sx126x`) and optionally the `lora-async` package if using the async
   examples (see main lora `README.md` in the above directory for details).
2. Edit the `lora_rd_settings.py` file to set the frequency and other protocol
   settings for your region and hardware (see main lora `README.md`).
3. Edit the program you plan to run and fill in the `get_modem()` function with
   the correct modem type, pin assignments, etc. for your board (see top-level
   README). Note the `get_modem()` function should use the existing `lora_cfg`
   variable, which holds the settings imported from `lora_rd_settings.py`.
4. Change to this directory in a terminal.
5. Run `mpremote mount . exec receiver.py` on one board and `mpremote mount
   . exec sender.py` on another (or swap in `receiver_async.py` and/or
   `sender_async.py` as desired).

Consult the [mpremote
documentation](https://docs.micropython.org/en/latest/reference/mpremote.html)
for an explanation of these commands and the options needed to run two copies of
`mpremote` on different serial ports at the same time.

## Automatic Performance Tuning

- When sending an ACK, the receiver includes the RSSI of the received
  packet. Senders will automatically modify their output_power to minimize the
  power consumption required to reach the receiver. Similarly, if no ACK is
  received then they will increase their output power and also re-run Image
  calibration in order to maximize RX performance.

## Message payloads

Messages are LoRa packets, set up as follows:

LoRA implicit header mode, CRCs enabled.

* Each remote device has a unique sixteen-bit ID (range 00x0000 to 0xFFFE). ID
  0xFFFF is reserved for the single receiver device.
* An eight-bit message counter is used to identify duplicate messages

* Data message format is:
  - Sender ID (two bytes, little endian)
  - Counter byte (incremented on each new message, not incremented on retry).
  - Message length (1 byte)
  - Message (variable length)
  - Checksum byte (sum of all proceeding bytes in message, modulo 256). The LoRa
    packet has its own 16-bit CRC, this is included as an additional way to
    disambiguate other LoRa packets that might appear the same.

* After receiving a valid data message, the receiver device should send
  an acknowledgement message 25ms after the modem receive completed.

  Acknowledgement message format:
  - 0xFFFF (receiver station ID as two bytes)
  - Sender's Device ID from received message (two bytes, little endian)
  - Counter byte from received message
  - Checksum byte from received message
  - RSSI value as received by radio (one signed byte)

* If the remote device doesn't receive a packet with the acknowledgement
  message, it retries up to a configurable number of times (default 4) with a
  basic exponential backoff formula.

