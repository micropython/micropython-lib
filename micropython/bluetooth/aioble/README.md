aioble
======

This library provides an object-oriented, asyncio-based wrapper for MicroPython's
[bluetooth](https://docs.micropython.org/en/latest/library/bluetooth.html) API.

**Note**: aioble requires MicroPython v1.17 or higher.

Features
--------

Broadcaster (advertiser) role:
* Generate advertising and scan response payloads for common fields.
* Automatically split payload over advertising and scan response.
* Start advertising (indefinitely or for duration).

Peripheral role:
* Wait for connection from central.
* Wait for MTU exchange.

Observer (scanner) role:
* Scan for devices (passive + active).
* Combine advertising and scan response payloads for the same device.
* Parse common fields from advertising payloads.

Central role:
* Connect to peripheral.
* Initiate MTU exchange.

GATT Client:
* Discover services, characteristics, and descriptors (optionally by UUID).
* Read / write / write-with-response characters and descriptors.
* Subscribe to notifications and indications on characteristics (via the CCCD).
* Wait for notifications and indications.

GATT Server:
* Register services, characteristics, and descriptors.
* Wait for writes on characteristics and descriptors.
* Intercept read requests.
* Send notifications and indications (and wait on response).

L2CAP:
* Accept and connect L2CAP Connection-oriented-channels.
* Manage channel flow control.

Security:
* JSON-backed key/secret management.
* Initiate pairing.
* Query encryption/authentication state.

All remote operations (connect, disconnect, client read/write, server indicate, l2cap recv/send, pair) are awaitable and support timeouts.

Installation
------------

You can install any combination of the following packages.
- `aioble-central` -- Central (and Observer) role functionality including
  scanning and connecting.
- `aioble-client` -- GATT client, typically used by central role devices but
  can also be used on peripherals.
- `aioble-l2cap` -- L2CAP Connection-oriented-channels support.
- `aioble-peripheral` -- Peripheral (and Broadcaster) role functionality
  including advertising.
- `aioble-security` -- Pairing and bonding support.
- `aioble-server` -- GATT server, typically used by peripheral role devices
  but can also be used on centrals.

Alternatively, install the `aioble` package, which will install everything.

Usage
-----

#### Passive scan for nearby devices for 5 seconds: (Observer)

```py
async with aioble.scan(duration_ms=5000) as scanner:
    async for result in scanner:
        print(result, result.name(), result.rssi, result.services())
```

Active scan (includes "scan response" data) for nearby devices for 5 seconds
with the highest duty cycle: (Observer)

```py
async with aioble.scan(duration_ms=5000, interval_us=30000, window_us=30000, active=True) as scanner:
    async for result in scanner:
        print(result, result.name(), result.rssi, result.services())
```

#### Connect to a peripheral device: (Central)

```py
# Either from scan result
device = result.device
# Or with known address
device = aioble.Device(aioble.PUBLIC, "aa:bb:cc:dd:ee:ff")

try:
    connection = await device.connect(timeout_ms=2000)
except asyncio.TimeoutError:
    print('Timeout')
```

#### Register services and wait for connection: (Peripheral, Server)

```py
_ENV_SENSE_UUID = bluetooth.UUID(0x181A)
_ENV_SENSE_TEMP_UUID = bluetooth.UUID(0x2A6E)
_GENERIC_THERMOMETER = const(768)

_ADV_INTERVAL_US = const(250000)

temp_service = aioble.Service(_ENV_SENSE_UUID)
temp_char = aioble.Characteristic(temp_service, _ENV_SENSE_TEMP_UUID, read=True, notify=True)

aioble.register_services(temp_service)

while True:
    connection = await aioble.advertise(
            _ADV_INTERVAL_US,
            name="temp-sense",
            services=[_ENV_SENSE_UUID],
            appearance=_GENERIC_THERMOMETER,
            manufacturer=(0xabcd, b"1234"),
        )
    print("Connection from", device)
```

#### Update characteristic value: (Server)

```py
# Write the local value.
temp_char.write(b'data')
```

```py
# Write the local value and notify/indicate subscribers.
temp_char.write(b'data', send_update=True)
```

#### Send notifications: (Server)

```py
# Notify with the current value.
temp_char.notify(connection)
```

```py
# Notify with a custom value.
temp_char.notify(connection, b'optional data')
```

#### Send indications: (Server)

```py
# Indicate with current value.
await temp_char.indicate(connection, timeout_ms=2000)
```

```py
# Indicate with custom value.
await temp_char.indicate(connection, b'optional data', timeout_ms=2000)
```

This will raise `GattError` if the indication is not acknowledged.

#### Wait for a write from the client: (Server)

```py
# Normal characteristic, returns the connection that did the write.
connection = await char.written(timeout_ms=2000)
```

```py
# Characteristic with capture enabled, also returns the value.
char = Characteristic(..., capture=True)
connection, data = await char.written(timeout_ms=2000)
```

#### Query the value of a characteristic: (Client)

```py
temp_service = await connection.service(_ENV_SENSE_UUID)
temp_char = await temp_service.characteristic(_ENV_SENSE_TEMP_UUID)

data = await temp_char.read(timeout_ms=1000)
```

#### Wait for a notification/indication: (Client)

```py
# Notification
data = await temp_char.notified(timeout_ms=1000)
```

```py
# Indication
data = await temp_char.indicated(timeout_ms=1000)
```

#### Subscribe to a characteristic: (Client)

```py
# Subscribe for notification.
await temp_char.subscribe(notify=True)
while True:
    data = await temp_char.notified()
```

```py
# Subscribe for indication.
await temp_char.subscribe(indicate=True)
while True:
    data = await temp_char.indicated()
```

#### Open L2CAP channels: (Listener)

```py
channel = await connection.l2cap_accept(_L2CAP_PSN, _L2CAP_MTU)
buf = bytearray(64)
n = channel.recvinto(buf)
channel.send(b'response')
```

#### Open L2CAP channels: (Initiator)

```py
channel = await connection.l2cap_connect(_L2CAP_PSN, _L2CAP_MTU)
channel.send(b'request')
buf = bytearray(64)
n = channel.recvinto(buf)
```


Examples
--------

See the `examples` directory for some example applications.

* temp_sensor.py: Temperature sensor peripheral.
* temp_client.py: Connects to the temp sensor.
* l2cap_file_server.py: Simple file server peripheral. (WIP)
* l2cap_file_client.py: Client for the file server. (WIP)

Tests
-----

The `multitests` directory provides tests that can be run with MicroPython's `run-multitests.py` script. These are based on the existing `multi_bluetooth` tests that are in the main repo.
