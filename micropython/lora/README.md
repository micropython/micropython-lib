# LoRa driver

This MicroPython library provides synchronous and asynchronous wireless drivers
for Semtech's LoRa (Long Range Radio) modem devices.

(LoRa is a registered trademark or service mark of Semtech Corporation or its
affiliates.)

## Support

Currently these radio modem chipsets are supported:

* SX1261
* SX1262
* SX1276
* SX1277
* SX1278
* SX1279
* STM32WL55 "sub-GHz radio" peripheral

Most radio configuration features are supported, as well as transmitting or
receiving packets.

This library can be used on any MicroPython port which supports the `machine.SPI`
interface.

## Installation

First, install at least one of the following "base" LoRa packages:

- `lora-sync` to use the synchronous LoRa modem API.
- `lora-async` to use the asynchronous LoRa modem API with
  [asyncio](https://docs.micropython.org/en/latest/library/asyncio.html). Support
  for `asyncio` must be included in your MicroPython build to use `lora-async`.

Second, install at least one of the following modem chipset drivers for the
modem model that matches your hardware:

- `lora-sx126x` for SX1261 & SX1262 support.
- `lora-sx127x` for SX1276-SX1279 support.
- `lora-stm32wl5` for STM32WL55 support.

It's recommended to install only the packages that you need, to save firmware
size.

Installing any of these packages will automatically also install a common
base package, `lora`.

For more information about how to install packages, or "freeze" them into a
firmware image, consult the [MicroPython documentation on "Package
management"](https://docs.micropython.org/en/latest/reference/packages.html).

## Initializing Driver

### Creating SX1262 or SX1261

This is the synchronous modem class, and requires `lora-sync` to be installed:

```py
from machine import SPI, Pin
import lora import SX1262  # or SX1261, depending on which you have

def get_modem():
    # The LoRa configuration will depend on your board and location, see
    # below under "Modem Configuration" for some possible examples.
    lora_cfg = { 'freq_khz': SEE_BELOW_FOR_CORRECT_VALUE }

    # To instantiate SPI correctly, see
    # https://docs.micropython.org/en/latest/library/machine.SPI.html
    spi = SPI(0, baudrate=2000_000)
    cs = Pin(9)

    # or SX1261(), depending on which you have
    return SX1262(spi, cs,
                 busy=Pin(2),  # Required
                 dio1=Pin(20),   # Optional, recommended
                 reset=Pin(15),  # Optional, recommended
                 lora_cfg=lora_cfg)

modem = get_modem()
```

### Creating SX127x

This is the synchronous modem class, and requires `lora-sync` to be installed:

```py
from machine import SPI, Pin
# or SX1277, SX1278, SX1279, depending on which you have
from lora import SX1276

def get_modem():
    # The LoRa configuration will depend on your board and location, see
    # below under "Modem Configuration" for some possible examples.
    lora_cfg = { 'freq_khz': SEE_BELOW_FOR_CORRECT_VALUE }

    # To instantiate SPI correctly, see
    # https://docs.micropython.org/en/latest/library/machine.SPI.html
    spi = SPI(0, baudrate=2000_000)
    cs = Pin(9)

    # or SX1277, SX1278, SX1279, depending on which you have
    return SX1276(spi, cs,
                  dio0=Pin(10),  # Optional, recommended
                  dio1=Pin(11),  # Optional, recommended
                  reset=Pin(13),  # Optional, recommended
                  lora_cfg=lora_cfg)

modem = get_modem()
```

*Note*: Because SX1276, SX1277, SX1278 and SX1279 are very similar, currently
the driver uses the same code for any. Dealing with per-part limitations (for
example: lower max frequency, lower maximum SF value) is responsibility of the
calling code. When possible please use the correct class anyhow, as per-part
code may be added in the future.

### Creating STM32WL55

```
from lora import WL55SubGhzModem

def get_modem():
    # The LoRa configuration will depend on your board and location, see
    # below under "Modem Configuration" for some possible examples.
    lora_cfg = { 'freq_khz': SEE_BELOW_FOR_CORRECT_VALUE }
    return WL55SubGhzModem(lora_cfg)

modem = get_modem()
```

Note: As this is an internal peripheral of the STM32WL55 microcontroller,
support also depends on MicroPython being built for a board based on this
microcontroller.

### Notes about initialisation

* See below for details about the `lora_cfg` structure that configures the modem's
  LoRa registers.
* Connecting radio "dio" pins as shown above is optional but recommended so the
  driver can use pin interrupts for radio events. If not, the driver needs to
  poll the chip instead. Interrupts allow reduced power consumption and may also
  improve receive sensitivity (by removing SPI bus noise during receive
  operations.)

### All constructor parameters

Here is a full list of parameters that can be passed to both constructors:

#### S1261/SX1262

(Note: It's important to instantiate the correct object as these two modems have small differences in their command protocols.)

| Parameter                 | Required               | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
|---------------------------|------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `spi`                     | Yes                    | Instance of a `machine.SPI` object or compatible, for the modem's SPI interface (modem MISO, MOSI, SCK pins).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| `cs`                      | Yes                    | Instance of a `machine.Pin` input, as connected to the modem's NSS pin.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| `busy`                    | Yes                    | Instance of a `machine.Pin` input, as connected to the modem's BUSY pin.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| `dio1`                    | No                     | Instance of a `machine.Pin` input, as connected to the modem's DIO1 pin. If not provided then interrupts cannot be used to detect radio events.                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| `dio2_rf_sw`              | No, defaults to `True` | By default, configures the modem's DIO2 pin as an RF switch. The modem will drive this pin high when transmitting and low otherwise. Set this parameter to False if DIO2 is connected elsewhere on your LoRa board/module and you don't want it toggling on transmit.                                                                                                                                                                                                                                                                                                                                                 |
| `dio3_tcxo_millivolts`    | No                     | If set to an integer value, DIO3 will be used as a variable voltage source for the modem's main TCXO clock source. DIO3 will automatically disable the TCXO to save power when the 32MHz clock source is not needed. The value is units of millivolts and should be one of the voltages listed in the SX1261 datasheet section 13.3.6 "SetDIO3AsTCXOCtrl". Any value between `1600` and `3300` can be specified and the driver will round down to a lower supported voltage step if necessary. The manufacturer of the LoRa board or module you are using should be able to tell you what value to pass here, if any. |
| `dio3_tcxo_start_time_us` | No                     | This value is ignored unless `dio3_tcxo_millivolts` is set, and is the startup delay in microseconds for the TCXO connected to DIO3. Each time the modem needs to enable the TCXO, it will wait this long. The default value is `1000` (1ms). Values can be set in multiples of `15.625`us and range from 0us to 262 seconds (settings this high will make the modem unusable).                                                                                                                                                                                                                                           |
| reset               | No                     | If set to a `machine.Pin` output attached to the modem's NRESET pin , then it will be used to hard reset the modem before initializing it. If unset, the programmer is responsible for ensuring the modem is in an idle state when the constructor is called.                                                                                                                                                                                                                                                                                                                                                         |
| `lora_cfg`                | No                     | If set to an initial LoRa configuration then the modem is set up with this configuration. If not set here, can be set by calling `configure()` later on.                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| `ant_sw`                  | No                     | Optional antenna switch object instance, see below for description.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |


#### SX1276/SX1277/SX1278/SX1279

| Parameter   | Required | Description                                                                                                                                                                                                                                                      |   |
|-------------|----------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---|
| `spi`         | Yes      | Instance of a `machine.SPI` object or compatible, for the modem's SPI interface (modem MISO, MOSI, SCK pins).                                                                                                                                                    |   |
| `cs`          | Yes      | Instance of a `machine.Pin` input, as connected to the modem's NSS pin.                                                                                                                                                                                          |   |
| `dio0`        | No       | Instance of a `machine.Pin` input, as connected to the modem's DIO0 pin. If set, allows the driver to use interrupts to detect "RX done" and "TX done" events.                                                                                                   |   |
| `dio1`        | No       | Instance of a `machine.Pin` input, as connected to the modem's DIO1/DCLK pin. If set, allows the driver to use interrupts to detect "RX timeout" events. Setting this pin requires dio0 to also be set.                                                          |   |
| `reset` | No       | If set to a `machine.Pin` output attached the modem's NRESET pin , it will be used to hard reset the modem before initializing it. If unset, the programmer is responsible for ensuring the modem should be is in an idle state when the object is instantiated. |   |
| `lora_cfg`    | No       | If set to an initial LoRa configuration then the modem is set up with this configuration. If not set here, can be set by calling `configure()` later on.                                                                                                         |   |
| `ant`_sw      | No       | Optional antenna switch object instance, see below for description.                                                                                                                                                                                              |   |

#### STM32WL55

| Parameter         | Required | Description                                                                                                                                                                    |
|-------------------|----------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `lora_cfg`        | No       | If set to an initial LoRa configuration then the modem is set up with this configuration. If not set here, can be set by calling `configure()` later on.                       |
| `tcxo_millivolts` | No       | Defaults to 1700. The voltage supplied on pin PB0_VDDTCXO. See `dio3_tcxo_millivolts` above for details, this parameter has the same behaviour.                                |
| ant_sw            | No       | Defaults to an instance of `lora.NucleoWL55RFConfig` class for the NUCLEO-WL55 development board. Set to `None` to disable any automatic antenna switching. See below for description.                               |


## Modem Configuration

It is necessary to correctly configure the modem before use. At minimum, the
correct RF frequency must be set. There are many additional LoRa modem radio
configuration settings that may be important. For two LoRa modem modems to
communicate, their radio configurations must be compatible.

**Different regions in the world also have RF regulations which you must abide
by. Check RF communications regulations for the location you are in, to
determine which configurations are legal for you to use.**

Modem configuration can be set in two ways:

- Pass `lora_cfg` keyword parameter to the modem class constructor (see examples
  above).
- Call `modem.configure(lora_cfg)` at any time

Where `lora_cfg` is a `dict` containing configuration keys and values. If a key
is missing, the value set in the modem is unchanged.

### Basic Configuration

The minimal configuration is the modem frequency:

```py
lora_cfg = { 'freq_khz': 916000 }
modem.configure(lora_cfg)
```

The example above sets the main frequency to 916.0MHz (916,000kHz), and leaves
the rest of the modem settings at their defaults. If you have two of the same
module using this driver, setting the same frequency on both like this may be
enough for them to communicate. However, the other default settings are a
compromise that may not give the best range, bandwidth, reliability, etc. for
your application. The defaults may not even be legal to transmit with in your
region!

Other parameters, particularly Bandwidth (`lora_cfg["bw"]`), Spreading Factor
(`lora_cfg["sf"]`), and transmit power (`lora_cfg["output_power"]`) may be
limited in your region. You should find this out as well and ensure the
configuration you are using is allowed. **This is your responsibility!**

#### Defaults

If you don't configure anything, the default settings are equivalent to:

```py
lora_cfg = { 'freq_khz': None, # Must set this
             'sf': 7,
             'coding_rate': 5,  # 4/5 Coding
             'bw': '125',
             }
```

With the default `output_power` level depending on the radio in use.

#### Choosing Other Parameters

Valid choices are determined by two things:

- Regulatory rules in your region. This information is provided by regional
  authorities, but it may also be useful to consult the [LoRaWAN Regional
  Parameters document
  (official)](https://resources.lora-alliance.org/technical-specifications/rp002-1-0-4-regional-parameters)
  and the ([Things Network
  (unofficial)](https://www.thethingsnetwork.org/docs/lorawan/regional-parameters/)
  for LoRaWAN frequency plans.

  Even if you're not connecting to a LoRaWAN network, if you choose frequency
  and bandwidth settings from the LoRaWAN recommendations for your region then
  they should be legal to use.
- Design of the radio module/modem/board you are using. RF antenna components
  are usually tailored for particular frequency ranges. One some boards only
  particular antenna ports or other features may be connected.

#### Longer Range Configuration

Here is an example aiming for higher range and lower data rate with the main
frequency set again to 916Mhz (for the "AU915" Australian region):

```py
lora_cfg = { 'freq_khz': 916000,
             'sf': 12,
             'bw': '62.5',  # kHz
             'coding_rate': 8,
             'output_power': 20,  # dBm
             'rx_boost': True,
         }
```

Quick explanation of these settings, for more detailed explanations see the next
section below:

* Setting `sf` to maximum (higher "Spreading Factor") means each LoRa "chirp"
  takes longer, for more range but lower data rate.
* Setting `bw` bandwidth setting lower makes the signal less susceptible to
  noise, but again slower. 62.5kHz is the lowest setting recommended by Semtech
  unless the modem uses a TCXO for high frequency stability, rather than a
  cheaper crystal.
* Setting `coding_rate` higher to 4/8 means that more Forward Error Correction
  information is sent, slowing the data rate but increasing the chance of a
  packet being received correctly.
* Setting `output_power` to 20dBm will select the maximum (or close to it) for
  the radio, which may be less than 20dBm.
* Enabling `rx_boost` will increase the receive sensitivity of the radio, if
  it supports this.

<details>
<summary>Additional Australia-specific regulatory explanation</summary>

The LoRaWAN AU915 specifications suggest 125kHz bandwidth. To tell that it's OK
to set `bw` lower, consult the Australian [Low Interference Potential Devices
class license](https://www.legislation.gov.au/Series/F2015L01438). This class
license allows Digital Modulation Transmitters in the 915-928MHz band to
transmit up to 1W Maximum EIRP provided "*The radiated peak power spectral
density in any 3 kHz must not exceed 25 mW per 3 kHz*".

`output_power` set to 20dBm is 100mW, over 62.5kHz bandwidth gives
1.6mW/kHz. This leaves significant headroom for antenna gain that might increase
radiated power in some directions.)
</details>

### Configuration Keys

These keys can be set in the `lora_cfg` dict argument to `configure()`,
and correspond to the parameters documented in this section.

Consult the datasheet for the LoRa modem you are using for an in-depth
description of each of these parameters.

Values which are unset when `configure()` is called will keep their existing
values.

#### `freq_khz` - RF Frequency
Type: `int` (recommended) or `float` (if supported by port)

LoRa RF frequency in kHz. See above for notes about regulatory limits on this
value.

The antenna and RF matching components on a particular LoRa device may only
support a particular frequency range. Consult the manufacturer's documentation.

#### `sf` - Spreading Factor
Type: `int`

Spreading Factor, numeric value only. Higher spreading factors allow reception
of weaker signals but have slower data rate.

The supported range of SF values varies depending on the modem chipset:

| Spreading Factor | Supported SX126x | Supported SX127x      |
|------------------|------------------|-----------------------|
| 5                | Yes              | **No**                |
| 6                | **Yes** [*]      | **Yes** [*]           |
| 7                | Yes              | Yes                   |
| 8                | Yes              | Yes                   |
| 9                | Yes              | Yes                   |
| 10               | Yes              | Yes, except SX1277[^] |
| 11               | Yes              | Yes, except SX1277[^] |
| 12               | Yes              | Yes, except SX2177[^] |

[*] SF6 is not compatible between SX126x and SX127x chipsets.

[^] SX1276, SX1278 and SX1279 all support SF6-SF12. SX1277 only supports
SF6-SF9. This limitation is not checked by the driver.

#### `bw` - Bandwidth
Type: `int` or `str`

Default: 125

Bandwidth value in kHz. Must be exactly one of these LoRa bandwidth values:

* 7.8
* 10.4
* 15.6
* 20.8
* 31.25
* 41.7
* 62.5
* 125
* 250
* 500

Higher bandwidth transmits data faster and reduces peak spectral density when
transmitting, but is more susceptible to interference.

IF setting bandwidth below 62.5kHz then Semtech recommends using a hardware TCXO
as the modem clock source, not a cheaper crystal. Consult the modem datasheet
and your hardware maker's reference for more information and to determine which
clock source your LoRa modem hardware is using.

For non-integer bandwidth values, it's recommended to always set this parameter
as a `str` (i.e. `"15.6"`) not a numeric `float`.

#### `coding_rate` - FEC Coding Rate
Type: `int`

Default: 5

Forward Error Correction (FEC) coding rate is expressed as a ratio, `4/N`. The
value passed in the configuration is `N`:

| Value | Error coding rate |
|-------|-------------------|
| 5     | 4/5               |
| 6     | 4/6               |
| 7     | 4/7               |
| 8     | 4/8               |

Setting a higher value makes transmission slower but increases the chance of
receiving successfully in a noisy environment

In explicit header mode (the default), `coding_rate` only needs to be set by the
transmitter and the receiver will automatically choose the correct rate when
receiving based on the received header. In implicit header mode (see
`implicit_header`), this value must be set the same on both transmitter and
receiver.

#### `tx_ant` - TX Antenna
Supported: *SX127x only*.

Type: `str`, not case sensitive

Default: RFO_HF or RFO_LF (low power)

SX127x modems and STM32WL55 microcontrollers have multiple antenna pins for
different power levels and frequency ranges. The board/module that the LoRa
modem chip is on may have particular antenna connections, or even an RF switch
that needs to be set via a GPIO to connect an antenna pin to a particular output
(see `ant_sw`, below).

The driver must configure the modem to use the correct pin for a particular
hardware antenna connection before transmitting. When receiving, the modem
chooses the correct pin based on the selected frequency.

A common symptom of incorrect `tx_ant` setting is an extremely weak RF signal.

Consult modem datasheet for more details.

##### SX127x tx_ant

| Value           | RF Transmit Pin                  |
|-----------------|----------------------------------|
| `"PA_BOOST"`    | PA_BOOST pin (high power)        |
| Any other value | RFO_HF or RFO_LF pin (low power) |

Pin "RFO_HF" is automatically used for frequencies above 862MHz, and is not
supported on SX1278. "RFO_LF" is used for frequencies below 862MHz. Consult
datasheet Table 32 "Frequency Bands" for more details.

##### WL55SubGhzModem tx_ant

| Value           | RF Transmit Pin         |
|-----------------|-------------------------|
| `"PA_BOOST"`    | RFO_HP pin (high power) |
| Any other value | RFO_LP pin (low power)  |

**NOTE**: Currently the `PA_BOOST` HP antenna output is lower than it should be
on this board, due to an unknown driver bug.

If setting `tx_ant` value, also set `output_power` at the same time or again
before transmitting.

#### `output_power` - Transmit output power level
Type: `int`

Default: Depends on modem

Nominal TX output power in dBm. The possible range depends on the modem and for
some modems the `tx_ant` configuration.

| Modem           | `tx_ant` value             | Range (dBm)       | "Optimal" (dBm)        |   |
|-----------------|----------------------------|-------------------|------------------------|---|
| SX1261          | N/A                        | -17 to +15        | +10, +14 or +15 [*][^] |   |
| SX1262          | N/A                        | -9 to +22         | +14, +17, +20, +22 [*] |   |
| SX127x          | "PA_BOOST"                 | +2 to +17, or +20 | Any                    |   |
| SX127x          | RFO_HF or RFO_LF           | -4 to +15         | Any                    |   |
| WL55SubGhzModem | "PA_BOOST"                 | -9 to +22         | +14, +17, +20, +22 [*] |   |
| WL55SubGhzModem | Any other value (not None) | -17 to +14        | +10, +14 or +15 [*][^] |   |

Values which are out of range for the modem will be clamped at the
minimum/maximum values shown above.

Actual radiated TX power for RF regulatory purposes depends on the RF hardware,
antenna, and the rest of the modem configuration. It should be measured and
tuned empirically not determined from this configuration information alone.

[*] For some modems the datasheet shows "Optimal" Power Amplifier
configuration values for these output power levels. If setting one of these
levels, the optimal settings from the datasheet are applied automatically by the
driver. Therefore it is recommended to use one of these power levels if
possible.

[^] In the marked configurations +15dBm is only possible with frequency above
400MHz, will be +14dBm otherwise.

#### `implicit_header` - Implicit/Explicit Header Mode
Type: `bool`

Default: `False`

LoRa supports both implicit and explicit header modes. Explicit header mode
(`implicit_header` set to False) is the default.

`implicit_header` must be set the same on both sender and receiver.

* In explicit header mode (default), each transmitted LoRa packet has a header
  which contains information about the payload length, `coding_rate` value in
  use, and whether the payload has a CRC attached (`crc_en`). The receiving
  modem decodes and verifies the header and uses the values to receive the
  correct length payload and verify the CRC if enabled.
* In implicit header mode (`implicit_header` set to True), this header is not
  sent and this information must be already be known and configured by both
  sender and receiver. Specifically:
  - `crc_en` setting should be set the same on both sender and receiver.
  - `coding_rate` setting must match between the sender and receiver.
  - Receiver must provide the `rx_length` argument when calling either
    `recv()` or `start_recv()`. This length must match the length in bytes
    of the payload sent by the sender.

### `crc_en` - Enable CRCs
Type: `bool`

Default: `True`

LoRa packets can have a 16-bit CRC attached to determine if a packet is
received correctly without corruption.

* In explicit header mode (default), the sender will attach a CRC if
  `crc_en` is True. `crc_en` parameter is ignored by the receiver, which
  determines if there is a CRC based on the received header and will check it if
  so.
* In implicit header mode, the sender will only include a CRC if `crc_en`
  is True and the receiver will only check the CRC if `crc_en` is True.

By default, if CRC checking is enabled on the receiver then the LoRa modem driver
silently drops packets with invalid CRCs. Setting `modem.rx_crc_error = True`
will change this so that packets with failed CRCs are returned to the caller,
with the `crc_error` field set to True (see `RxPacket`, below).

#### `auto_image_cal` - Automatic Image Calibration
Supported: *SX127x only*.

Type: `bool`

Default: `False`

If set True, enable automatic image re-calibration in the modem if the
temperature changes significantly. This may avoid RF performance issues caused
by frequency drift, etc. Setting this value may lead to dropped packets received
when an automatic calibration event is in progress.

Consult SX127x datasheet for more information.

#### `syncword` - Sync Word
Type: `int`

Default: `0x12`

LoRa Sync Words are used to differentiate LoRa packets as being for Public or
Private networks. Sync Word must match between sender and receiver.

For SX127x this value is an 8-bit integer. Supported values 0x12 for Private
Networks (default, most users) and 0x34 for Public Networks (LoRaWAN only).

For SX126x this value is a 16-bit integer. Supported values 0x1424 for Private

Networks (default, most users) and 0x3444 for Public Networks. However the
driver will automatically [translate values configured using the 8-bit SX127x
format](https://www.thethingsnetwork.org/forum/t/should-private-lorawan-networks-use-a-different-sync-word/34496/15)
for software compatibility, so setting an 8-bit value is supported on all modems.

You probably shouldn't change this value from the default, unless connecting to
a LoRaWAN network.

#### `pa_ramp_us` - PA Ramp Time
Type: `int`

Default: `40`us

Power Amplifier ramp up/down time, as expressed in microseconds.

The exact values supported on each radio are different. Configuring an
unsupported value will cause the driver to choose the next highest value that is
supported for that radio.

| Value (us) | Supported SX126x | Supported SX127x |
|------------|------------------|------------------|
| 10         | Yes              | Yes              |
| 12         | No               | Yes              |
| 15         | No               | Yes              |
| 20         | Yes              | Yes              |
| 25         | No               | Yes              |
| 31         | No               | Yes              |
| 40         | Yes              | Yes              |
| 50         | No               | Yes              |
| 62         | No               | Yes              |
| 80         | Yes              | No               |
| 100        | No               | Yes              |
| 125        | No               | Yes              |
| 200        | Yes              | No               |
| 250        | No               | Yes              |
| 500        | No               | Yes              |
| 800        | Yes              | No               |
| 1000       | No               | Yes              |
| 1700       | Yes              | No               |
| 2000       | No               | Yes              |
| 3400       | Yes              | Yes              |

#### `preamble_len` - Preamble Length
Type: `int`
Default: `12`

Length of the preamble sequence, in units of symbols.

#### `invert_iq_tx`/`invert_iq_rx` - Invert I/Q
Type: `bool`

Default: Both `False`

If `invert_iq_tx` or `invert_iq_rx` is set then IQ polarity is inverted in the
radio for either TX or RX, respectively. The receiver's `invert_iq_rx` setting
must match the sender's `invert_iq_tx` setting.

This is necessary for LoRaWAN where end-devices transmit with inverted IQ
relative to gateways.

Note: The current SX127x datasheet incorrectly documents the modem register
setting corresponding to `invert_iq_tx`. This driver configures TX polarity
correctly for compatibility with other LoRa modems, most other SX127x drivers,
and LoRaWAN. However, there are some SX127x drivers that follow the datasheet
description, and they will set `invert_iq_tx` opposite to this.

#### `rx_boost` - Boost receive sensitivity
Type: `bool`

Default: `False`

Enable additional receive sensitivity if available.

* On SX126x, this makes use of the "Rx Boosted gain" option.
* On SX127x, this option is available for HF bands only and sets the LNA boost
  register field.

#### `lna_gain` - Receiver LNA gain
Supported: *SX127x only*.

Type: `int` or `None`

Default: `1`

Adjust the LNA gain level for receiving. Valid values are `None` to enable
Automatic Gain Control, or integer gain levels 1 to 6 where 1 is maximum gain
(default).

## Sending & Receiving

### Simple API

The driver has a "simple" API to easily send and receive LoRa packets. The
API is fully synchronous, meaning the caller is blocked until the LoRa operation
(send or receive) is done. The Simple API doesn't support starting a
send while a receive in progress (or vice versa). It is suitable for simple
applications only.

For an example that uses the simple API, see `examples/reliable_delivery/sender.py`.

#### send

To send (transmit) a LoRa packet using the configured modulation settings:

```py
def send(self, packet, tx_at_ms=None)
```

Example:

```py
modem.send(b'Hello world')
```

* `send()` transmits a LoRa packet with the provided payload bytes, and returns
  once transmission is complete.
* The return value is the timestamp when transmission completed, as a
  `time.ticks_ms()` result. It will be more accurate if the modem was
  initialized to use interrupts.

For precise timing of sent packets, there is an optional `tx_at_ms` argument
which is a timestamp (as a `time.ticks_ms()` value). If set, the packet will be
sent as close as possible to this timestamp and the function will block until
that time arrives:

```py
modem.send(b'Hello world', time.ticks_add(time.ticks_ms(), 250))
```

(This allows more precise timing of sent packets, without needing to account for
the length of the packet to be copied to the modem.)

### receive

```py
def recv(self, timeout_ms=None, rx_length=0xFF, rx_packet=None)
```

Examples:

```py
with_timeout = modem.recv(2000)

print(repr(with_timeout))

wait_forever = modem.recv()

print(repr(wait_forever))
```

* `recv()` receives a LoRa packet from the modem.
* Returns None on timeout, or an `RxPacket` instance with the packet on
  success.
* Optional arguments:
   - `timeout_ms`. Optional, sets a receive timeout in milliseconds. If None
   (default value), then the function will block indefinitely until a packet is
   received.
   - `rx_length`. Necessary to set if `implicit_header` is set to `True` (see
     above). This is the length of the packet to receive. Ignored in the default
     LoRa explicit header mode, where the received radio header includes the
     length.
   - `rx_packet`. Optional, this can be an `RxPacket` object previously
     received from the modem. If the newly received packet has the same length,
     this object is reused and returned to save an allocation. If the newly
     received packet has a different length, a new `RxPacket` object is
     allocated and returned instead.

### RxPacket

`RxPacket` is a class that wraps a `bytearray` holding the LoRa packet payload,
meaning it can be passed anywhere that accepts a buffer object (like `bytes`,
`bytearray`).

However it also has the following metadata object variables:

* `ticks_ms` - is a timestamp of `time.ticks_ms()` called at the time the
    packet was received. Timestamp will be more accurate if the modem was
    initialized to use interrupts.
* `snr` - is the Signal to Noise ratio of the received packet, in units of `dB *
    4`. Higher values indicate better signal.
* `rssi` - is the Received Signal Strength indicator value in units of
    dBm. Higher (less negative) values indicate more signal strength.
* `crc_error` - In the default configuration, this value will always be False as
  packets with invalid CRCs are dropped. If the `modem.rx_crc_error` flag is set
  to True, then a packet with an invalid CRC will be returned with this flag set
  to True.

  Note that CRC is only ever checked on receive in particular configurations,
  see the `crc_en` configuration item above for an explanation. If CRC is not
  checked on receive, and `crc_error` will always be False.

Example:

```py
rx = modem.recv(1000)

if rx:
    print(f'Received {len(rx)} byte packet at '
          f'{rx.ticks_ms}ms, with SNR {rx.snr} '
          f'RSSI {rx.rssi} valid_crc {rx.valid_crc}')
```

### Asynchronous API

Not being able to do anything else while waiting for the modem is very
limiting. Async Python is an excellent match for this kind of application!

To use async Python, first install `lora-async` and then instantiate the async
version of the LoRA modem class. The async versions have the prefix `Async` at
the beginning of the class name. For example:

```py
import asyncio
from lora import AsyncSX1276

def get_async_modem():
    # The LoRa configuration will depend on your board and location, see
    # below under "Modem Configuration" for some possible examples.
    lora_cfg = { 'freq_khz': SEE_BELOW_FOR_CORRECT_VALUE }

    # To instantiate SPI correctly, see
    # https://docs.micropython.org/en/latest/library/machine.SPI.html
    spi = SPI(0, baudrate=2000_000)
    cs = Pin(9)

    # or AsyncSX1261, AsyncSX1262, AsyncSX1277, AsyncSX1278, SX1279, etc.
    return AsyncSX1276(spi, cs,
                       dio0=Pin(10),  # Optional, recommended
                       dio1=Pin(11),  # Optional, recommended
                       reset=Pin(13),  # Optional, recommended
                       lora_cfg=lora_cfg)

modem = get_async_modem()

async def recv_coro():
    rx = await modem.recv(2000)
    if rx:
        print(f'Received: {rx}')
    else:
        print('Timeout!')


async def send_coro():
    counter = 0
    while True:
        await modem.send(f'Hello world #{counter}'.encode())
        print('Sent!')
        await asyncio.sleep(5)
        counter += 1

async def init():
    await asyncio.gather(
        asyncio.create_task(send_coro()),
        asyncio.create_task(recv_coro())
    )

asyncio.run(init())
```

For a more complete example, see `examples/reliable_delivery/sender_async.py`.

* The `modem.recv()` and `modem.send()` coroutines take the same
  arguments as the synchronous class' functions `recv()` and `send()`,
  as documented above.
* However, because these are async coroutines it's possible for other async
  tasks to execute while they are blocked waiting for modem operations.
* It is possible to await the `send()` coroutine while a `recv()`
  is in progress. The receive will automatically resume once the modem finishes
  sending. Send always has priority over receive.
* However, at most one task should be awaiting each of receive and send. For
  example, it's not possible for two tasks to `await modem.send()` at the
  same time.

#### Async Continuous Receive

An additional API provides a Python async iterator that will continuously
receive packets from the modem:

```py
async def keep_receiving():
    async for packet in am.recv_continuous():
        print(f'Received: {packet}')
```

For a more complete example, see `examples/reliable_delivery/receiver_async.py`.

Receiving will continue and the iterator will yield packets unless another task
calls `modem.stop()` or `modem.standby()` (see below for a description of these
functions).

Same as the async `recv()` API, it's possible for another task to send while
this iterator is in use.

## Low-Level API

This API allows other code to execute while waiting for LoRa operations, without
using asyncio coroutines.

This is a traditional asynchronous-style API that requires manual management of
modem timing, interrupts, packet timeouts, etc. It's very easy to write
spaghetti code with this API. If asyncio is available on your board, the async
Python API is probably an easier choice to get the same functionality with less
complicated code.

However, if you absolutely need maximum control over the modem and the rest of
your board then this may be the API for you!

### Receiving

```py
will_irq =  modem.start_recv(timeout_ms=1000, continuous=False)

rx = True
while rx is True:
    if will_irq:
        # Add code to sleep and wait for an IRQ,
        # if necessary call modem.irq_triggered() to verify
        # that the modem IRQ was actually triggered.
        pass
    rx = modem.poll_recv()

    # Do anything else you need the application to do

if rx:  # isinstance(rx, lora.RxPacket)
    print(f'Received: {rx}')
else:  # rx is False
    print('Timed out')
```

For an example that uses the low-level receive API for continuous receive, see
`examples/reliable_delivery/receiver.py`.

The steps to receive packet(s) with the low-level API are:

1. Call `modem.start_recv(timeout_ms=None, continuous=False, rx_length=0xFF)`.

   - `timeout_ms` is an optional timeout in milliseconds, same as the Simple API
     recv().
   - Set `continuous=True` for the modem to continuously receive and not go into
     standby after the first packet is received. If setting `continuous` to
     `True`, `timeout_ms` must be `None`.
   - `rx_length` is an optional argument, only used when LoRa implicit headers
     are configured.  See the Simple API description above for details.

   The return value of this function is truthy if interrupts will be used for
   the receive, falsey otherwise.
2. If interrupts are being used, wait for an interrupt to occur. Steps may include
   configuring the modem interrupt pins as wake sources and putting the host
   into a light sleep mode. See the general description of "Interrupts", below.

   Alternatively, if `timeout_ms` was set then caller can wait for at least the
   timeout period before checking if the modem received anything or timed out.

    It is also possible to simply call `poll_recv()` in a loop, but doing
    this too frequently may significantly degrade the RF receive performance
    depending on the hardware.

3. Call `modem.poll_recv()`. This function checks the receive state and
   returns a value indicating the current state:

   - `True` if the modem is still receiving and the caller should call this
     function again in the future. This can be caused by any of:

     * Modem is still waiting in 'single' mode (`continuous=False`) to receive a
       packet or time out.
     * Modem is in continuous receive mode so will always be receiving.
     * The modem is actually sending right now, but the driver will resume
       receiving after the send completes.
     * The modem received a packet with an invalid CRC (and `modem.rx_crc_error
       = False`). The driver has just now discarded it and resumed the modem
       receive operation.

   - `False` if the modem is not currently receiving. This can be caused by any
     of:

     * No receive has been started.
     * A single receive has timed out.
     * The receive was aborted. See the `standby()` and `sleep()` functions
       below.

   - An instance of the `RxPacket` class. This means the modem has received this
     packet since the last call to `poll_recv()`. Whether or not the modem is
     still receiving after this depends on whether the receive was started in
     `continuous` mode or not.)

4. If `poll_recv()` returned `True`, go back to step 2 and wait for the next
   opportunity to call `poll_recv()`. (Note that it's necessary to test using
   `is True` to distinguish between `True` and a new packet.)

It is possible to also send packets while receiving and looping between
steps 2 and 4. The driver will automatically suspend receiving and resume it
again once sending is done. It's OK to call either the Simple API
`send()` function or the low-level send API (see below) in order to do
this.

The purpose of the low-level API is to allow code to perform other unrelated
functions during steps 2 and 3. It's still recommended to call
`modem.poll_recv()` as soon as possible after a modem interrupt has
occurred, especially in continuous receive mode when multiple packets may be
received rapidly.

To cancel a receive in progress, call `modem.standby()` or `modem.sleep()`, see
below for descriptions of these functions.

*Important*: None of the MicroPython lora driver is thread-safe. It's OK for
different MicroPython threads to manage send and receive, but the caller is
responsible for adding locking so that different threads are not calling any
modem APIs concurrently. Async MicroPython may provide a cleaner and simpler
choice for this kind of firmware architecture.

### Sending

The low-level API for sending is similar to the low-level API for receiving:

1. Call `modem.prepare_send(payload)` with the packet payload. This will put
   the modem into standby (pausing receive if necessary), configure the modem
   registers, and copy the payload into the modem FIFO buffer.
2. Call `modem.start_send(packet)` to actually start sending.

   Sending is split into these two steps to allow accurate send
   timing. `prepare_send()` may take a variable amount of time to copy data
   to the modem, configure registers, etc. Then `start_send()` only performs
   the minimum fixed duration operation to start sending, so transmit
   should start very soon after this function is called.

   The return value of `start_send()` function is truthy if an interrupt is
   enabled to signal the send completing, falsey otherwise.

   Not calling both `prepare_send()` or `start_send()` in order, or
   calling any other modem functions between `prepare_send()` and
   `start_send()`, is not supported and will result in incorrect behaviour.

3. Wait for the send to complete. This is possible in any of three
   different ways:
   -  If interrupts are enabled, wait for an interrupt to occur. Steps may include
      configuring the modem interrupt pins as wake sources and putting the host
      into a light sleep mode. See the general description of "Interrupts", below.
   - Calculate the packet "time on air" by calling
     `modem.get_time_on_air_us(len(packet))` and wait at least this long.
   - Call `modem.poll_send()` in a loop (see next step) until it confirms
     the send has completed.
4. Call `modem.poll_send()` to check transmission state, and to
   automatically resume a receive operation if one was suspended by
   `prepare_send()`. The result of this function is one of:

    - `True` if a send is in progress and the caller
      should call again.

    - `False` if no send is in progress.

    - An `int` value. This is returned the first time `poll_send()` is
      called after a send ended. The value is the `time.ticks_ms()`
      timestamp of the time that the send completed. If interrupts are
      enabled, this is the time the "send done" ISR executed. Otherwise, it
      will be the time that `poll_send()` was just called.

   Note that `modem.poll_send()` returns an `int` only one time per
   successful transmission. Any subsequent calls will return `False` as there is
   no longer a send in progress.

   To abort a send in progress, call `modem.standby()` or `modem.sleep()`,
   see the descriptions of these functions below. Subsequent calls to
   `poll_send()` will return `False`.
5. If `poll_send()` returned `True`, repeat steps 3 through 5.

*Important*: Unless a transmission is aborted, `poll_send()` **MUST be
called** at least once after `start_send()` and should be repeatedly called
until it returns a value other than `True`. `poll_send()` can also be called
after a send is aborted, but this is optional. If `poll_send()` is not
called correctly then the driver's internal state will not correctly update and
no subsequent receive will be able to start.

It's also possible to mix the simple `send()` API with the low-level receive
API, if this is more convenient for your application.

### Interrupts

If interrupt pins are in use then it's important for a programmer using the
low-level API to handle interrupts correctly.

It's only possible to rely on interrupts if the correct hardware interrupt lines
are configured. Consult the modem reference datasheet, or check if the value of
`start_recv()` or `start_send()` is truthy, in order to know if hardware
interrupts can be used. Otherwise, the modem must be polled to know when an
operation has completed.

There are two kinds of interrupts:

* A hardware interrupt (set in the driver by `Pin.irq()`) will be triggered on
  the rising edge of a modem interrupt line (DIO0, DIO1, etc). The driver will
  attempt to configure these for `RX Done`, `RX Timeout` and `TX Done` events if
  possible and applicable for the modem operation, and will handle them.

  It's possible for the programmer to configure these pins as hardware wake sources
  and put the board into a low-power sleep mode, to be woken when the modem
  finishes its operation.
* A "soft" interrupt is triggered by the driver if an operation is aborted (see
  `standby()` and `sleep()`, below), or if a receive operation "soft times
  out". A receive "soft times out" if a receive is paused by a send
  operation and after the send operation completes then the timeout period
  for the receive has already elapsed. In these cases, the driver's radio ISR
  routine is called but no hardware interrupt occurs.

To detect if a modem interrupt has occurred, the programmer can use any of the
following different approaches:

* Port-specific functions to determine a hardware wakeup cause. Note that this
  can only detect hardware interrupts.
* Call the `modem.irq_triggered()` function. This is a lightweight function that
  returns True if the modem ISR has been executed since the last time a send
  or receive started. It is cleared when `poll_recv()` or `poll_send()`
  is called after an interrupt, or when a new operation is started. The idea is
  to use this as a lightweight "should I call `poll_recv()` or
  `poll_send()` now?" check function if there's no easy way to determine
  which interrupt has woken the board up.
* Implement a custom interrupt callback function and call
  `modem.set_irq_callback()` to install it. The function will be called if a
  hardware interrupt occurs, possibly in hard interrupt context. Refer to the
  documentation about [writing interrupt handlers][isr_rules] for more
  information. It may also be called if the driver triggers a soft interrupt.
  The `lora-async` modem classes install their own callback here, so it's not
  possible to mix this approach with the provided asynchronous API.
* Call `modem.poll_recv()` or `modem.poll_send()`. This takes more time
  and uses more power as it reads the modem IRQ status directly from the modem
  via SPI, but it also give the most definite result.

As a "belts and braces" protection against unknown driver bugs or modem bugs,
it's best practice to not rely on an interrupt occurring and to also include
some logic that periodically times out and polls the modem state "just in case".

## Other Functions

### CRC Error Counter

Modem objects have a variable `modem.crc_errors` which starts at `0` and
is incremented by one each time a received CRC error or packet header error is
detected by the modem. The programmer can read this value to know the current CRC
error count, and also write it (for example, to clear it periodically by setting
to `0`).

For an alternative method to know about CRC errors when they occur, set
`modem.rx_crc_error = True` (see `crc_en`, above, for more details.)

### Modem Standby

Calling `modem.standby()` puts the modem immediately into standby mode. In the
case of SX1261 and SX1262, the 32MHz oscillator is started.

Any current send or receive operations are immediately aborted.  The
implications of this depends on the API in use:

* The simple API does not support calling `standby()` while a receive or
  send is in progress.
* The async API handles this situation automatically. Any blocked `send()`
  or `recv()` async coroutine will return None. The `recv_continuous()`
  iterator will stop iterating.
* The low-level API relies on the programmer to handle this case. When the modem
  goes to standby, a "soft interrupt" occurs that will trigger the radio ISR and
  any related callback, but this is not a hardware interrupt so may not wake the
  CPU if the programmer has put it back to sleep. Any subsequent calls to
  `poll_recv()` or `poll_send()` will both return `(False, None)` as no
  operation is in progress. The programmer needs to ensure that any code that is
  blocking waiting for an interrupt has the chance to wake up and call
  `poll_recv()` and/or `poll_send()` to detect that the operation(s) have
  been aborted.

### Modem Sleep

Calling `modem.sleep()` puts the modem into a low power sleep mode with
configuration retention. The modem will automatically wake the next time an
operation is started, or can be woken manually by calling
`modem.standby()`. Waking the modem may take some time, consult the modem
datasheet for details.

As with `standby()`, any current send or receive operations are immediately
aborted. The implications of this are the same as listed for standby, above.

### Check if modem is idle

The `modem.is_idle()` function will return True unless the modem is currently
sending or receiving.

### Packet length calculations

Calling `modem.get_time_on_air_us(plen)` will return the "on air time" in
microseconds for a packet of length `plen`, according to the current modem
configuration. This can be used to synchronise modem operations, choose
timeouts, or predict when a send will complete.

Unlike the other modem API functions, this function doesn't interact with
hardware at all so it can be safely called concurrently with other modem APIs.

## Antenna switch object

The modem constructors have an optional `ant_sw` parameter which allows passing
in an antenna switch object to be called by the driver. This allows
automatically configuring some GPIOs or other hardware settings each time the
modem changes between TX and RX modes, and goes idle.

The argument should be an object which implements three functions: `tx(tx_arg)`,
`rx()`, and `idle()`. For example:

```py
class MyAntennaSwitch:
    def tx(self, tx_arg):
        ant_sw_gpio(1)  # Set GPIO high

    def rx(self):
        ant_sw_gpio(0)  # Set GPIO low

    def idle(self):
        pass
```

* `tx()` is called a short time before the modem starts sending.
* `rx()` is called a short time before the modem starts receiving.
* `idle()` is called at some point after each send or receive completes, and
  may be called multiple times.

The meaning of `tx_arg` depends on the modem:

* For SX127x it is `True` if the `PA_BOOST` `tx_ant` setting is in use (see
  above), and `False` otherwise.
* For SX1262 it is `True` (indicating High Power mode).
* For SX1261 it is `False` (indicating Low Power mode).
* For WL55SubGhzModem it is `True` if the `PA_BOOST` `tx_ant` setting is in use (see above), and `False` otherwise.

This parameter can be ignored if it's already known what modem and antenna is being used.

### WL55SubGhzModem ant_sw

When instantiating the `WL55SubGhzModem` and `AsyncWL55SubGHzModem` classes, the
default `ant_sw` parameter is not `None`. Instead, the default will instantiate
an object of type `lora.NucleoWL55RFConfig`. This implements the antenna switch
connections for the ST NUCLEO-WL55 development board (as connected to GPIO pins
C4, C5 and C3). See ST document [UM2592][ST-UM2592-p27] (PDF) Figure 18 for details.

When using these modem classes (only), to disable any automatic antenna
switching behaviour it's necessary to explicitly set `ant_sw=None`.

## Troubleshooting

Some common errors and their causes:

### RuntimeError: BUSY timeout

The SX1261/2 drivers will raise this exception if the modem's TCXO fails to
provide the necessary clock signal when starting a transmit or receive
operation, or moving into "standby" mode.

Sometimes, this means the constructor parameter `dio3_tcxo_millivolts` (see above)
must be set as the SX126x chip DIO3 output pin is the power source for the TCXO
connected to the modem.  Often this parameter should be set to `3300` (3.3V) but
it may be another value, consult the documentation for your LoRa modem module.

[isr_rules]: https://docs.micropython.org/en/latest/reference/isr_rules.html
[ST-UM2592-p27]: https://www.st.com/resource/en/user_manual/dm00622917-stm32wl-nucleo64-board-mb1389-stmicroelectronics.pdf#page=27
