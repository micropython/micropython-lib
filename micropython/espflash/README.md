# Build instructions for the NINA and esp_hosted firmware

# NINA firmware

The NINAW10 firmware only works with classic ESP32 devices. No support
for newer models like ESP32C3.

## Get the NINAW10 Arduino source code

The link is https://github.com/arduino/nina-fw.git. Follow the
instructions in the README.md document of the NINA firmware to
download the NINA firmware and the esp-idf.

## Get the ESP32 development environment.

The NINA firmware needs esp-idf v3.3.1 up to v3.3.4. After installing
the esp-idf version, run:

    ./install.sh  
    git submodule sync  
    git submodule update --init  
    . export.sh

in the esp-idf directory.

## Check the SPI and UART pins.

Change SPI pins at the end of this file:  

nina-fw-1.5.0-Arduino/arduino/libraries/SPIS/src/SPIS.cpp  

Suitable settings:

    // for Arduino NINA W102 modules:
    SPISClass SPIS(VSPI_HOST, 1, 12, 23, 18, 5, 33); // SPI-device, DMA-channel, MOSI, MISO, SCK, CS, ACK

    // for Airlift modules:
    SPISClass SPIS(VSPI_HOST, 1, 14, 23, 18, 5, 33); // SPI-device, DMA-channel, MOSI, MISO, SCK, CS, ACK


Change UART pins at about line 123 in this file: 

nina-fw-1.5.0-Arduino/main/sketch.ino.cpp

Suitable settings:

    // for Arduino NINA W102 modules:
    uart_set_pin(UART_NUM_1, 1, 3, 33, 12); // TX, RX, RTS, CTS

    //  for Airlift modules:
    uart_set_pin(UART_NUM_1, 1, 3, 33, 14); // TX, RX, RTS, CTS

The respective pin assignments can be found below in the pin table.
The only difference between the Adafruit Airlift and Arduino NINA-W102 modules
is for the RTS/MOSI pin. All Adafruit airlift modules
use the Airlift pin assignments, even when the hardware is a NINA-W102
module. If you use a custom ESP32 device and want to
use different pins, you can change the pin numbers as needed.

## Build the firmware

Call `make RELEASE=1 NANO_RP2040_CONNECT=1` to build the firmware.
Run combine.py with `python combine.py` to get a combined firmware
file, which can be loaded to the target module using e.g. espflash.py.
The file name will be `NINA_FW.bin`.

Sample script to create the combined firmware:

    #!/usr/bin/env python

    import sys;

    booloaderData = open("build/bootloader/bootloader.bin", "rb").read()
    partitionData = open("build/partitions.bin", "rb").read()
    phyData = open("data/phy.bin", "rb").read()
    certsData = open("data/roots.pem", "rb").read()
    appData = open("build/nina-fw.bin", "rb").read()

    # calculate the output binary size, app offset 
    outputSize = 0x30000 + len(appData)
    if (outputSize % 1024):
        outputSize += 1024 - (outputSize % 1024)

    # allocate and init to 0xff
    outputData = bytearray(b'\xff') * outputSize

    # copy data: bootloader, partitions, app
    for i in range(0, len(booloaderData)):
        outputData[0x1000 + i] = booloaderData[i]

    for i in range(0, len(partitionData)):
        outputData[0x8000 + i] = partitionData[i]

    for i in range(0, len(phyData)):
            outputData[0xf000 + i] = phyData[i]

    for i in range(0, len(certsData)):
            outputData[0x10000 + i] = certsData[i]

    # zero terminate the pem file
    outputData[0x10000 + len(certsData)] = 0

    for i in range(0, len(appData)):
        outputData[0x30000 + i] = appData[i]


    outputFilename = "NINA_FW.bin"
    if (len(sys.argv) > 1):
        outputFilename = sys.argv[1]

    # write out
    with open(outputFilename,"w+b") as f:
        f.seek(0)
        f.write(outputData)

The combined firmware file will be `NINA_FW.bin`. This
file can be loaded to the target module using e.g. espflash.py.

# Esp-hosted firmware

The esp-hosted firmware should work with all ESP32 modules. Tested with
a ESP32 classic and a ESP32C3.

## Get the esp-hosted source code

The source code repository is at:  

https://github.com/espressif/esp-hosted.git

The code for the esp-hosted network adapter is at:  

esp_hosted_fg/esp/esp_driver

The commit used for these instructions is `244b864`. Newer version are
not tested.

## Get the ESP32 development environment.

Follow the instructions in the README.md of micropython/ports/esp32.
Check out v5.5.1. Run in the esp-idf directory:

    ./install.sh  
    git submodule sync  
    git submodule update --init  
    . export.sh  

## Check the UART pins.

The UART pins for bluetooth are defined in the file:  

esp_hosted_fg/esp/esp_driver/network_adapter/main/slave_bt.h

The UART settings used for the Airlift module with ESP32 are:

    #define BT_TX_PIN           1
    #define BT_RX_PIN           3
    #define BT_RTS_PIN         14
    #define BT_CTS_PIN         33

The UART settings used for the Arduino NINA-W102 module with ESP32 are:

    #define BT_TX_PIN           1
    #define BT_RX_PIN           3
    #define BT_RTS_PIN         12
    #define BT_CTS_PIN         33

The respective pin assignments can be found in the table below.
The only difference between the Adafruit Airlift and Arduino NINA-W102 modules
is for the RTS/MOSI pin. If you use a custom ESP32 device and want to
use different pins, you can change the pin numbers as needed.

## Set the configuration in sdkconfig

The SPI and Bluetooth configuration is stored in the file sdkconfig. Call
`idf.py menuconfig` in a terminal window to create or modify the
sdkconfig configuration file.

Change/verify the settings as follows:

### SPI configuration

- At `Example Configuration → Transport layer` select `SPI`.
- At `Example Configuration → SPI Full-duplex Configuration → SPI controller to use` select VSPI.
- At `Example Configuration → SPI Full-duplex Configuration → Hosted SPI GPIOs`set the GPIO pins to MOSI=14 (Airlift) or 12 (Arduino W102), MISO=23, CLK=18, CS=5, handshake=33, data ready interupt=0, Reset=-1.  
- Clear `Example Configuration → SPI Full-duplex Configuration → Deassert Handshake when SPI CS is deasserted`
- Set `Example Configuration → SPI Full-duplex Configuration → SPI checksum ENABLE/DISABLE`.
- Set `Example Configuration → Enable Mempool`
- Set `Example Configuration → Start CLI at slave`
- Set `Example Configuration → Wi-Fi control` to `Host manages Wi-Fi`


### Bluetooth configuration.

- Set `Component config → Bluetooth → Bluetooth → Host` to Disabled.
- Set `Component config → Bluetooth → Bluetooth → Controller` to Enabled
- Set `Component config → Bluetooth → Controller Options → Bluetooth controller mode (BR/EDR/BLE/DUALMODE)` to `BLE Only`.
- Set `Component config → Bluetooth → Controller Options → HCI mode` to `UART(H4)`.
- In  `Component config → Bluetooth → Controller Options → HCI UART(H4)` select UART 1, 460800 Baud and **disable flow control**.

### PHY config

- At `Component config → PHY` set `Max WiFi TX power` to 20 (default).
- AT `Component config → PHY` enable `Reduce PHY TX power when brownout reset`

After that, save the configuration by pressing the letter 'S'. That
creates the file skdconfig or rewrites it after changes. 

## Build the firmware

Build the firmware using:

idf.py build

Create the combined firmware with the command:

python -m esptool --chip esp32  merge_bin --flash_mode dio --flash_size keep --flash_freq 40m -o esp_hosted.bin 0x1000 build/bootloader/bootloader.bin 0x8000 build/partition_table/partition-table.bin 0xd000 build/ota_data_initial.bin 0x10000 build/network_adapter.bin

The combined firmware file will be `esp_hosted.bin`. This
file can be installed in the target module using e.g. espflash.py.


# NINA FW and esp-hosted names and pins assignments

Mapping between firmware signal names for the NINA
firmware and esp_hosted firmware and the ESP32 pins of Arduino
and Adafruit Airlift modules.

    ========  ========== ========  =======  =======
    NINA FW   esp_hosted Arduino   Airlift  Airlift
    Name      FW Name    W102 Pin  Label    Pin
    ========  ========== ========  =======  =======
    MOSI      MOSI         12      MOSI       14
    MISO      MISO         23      MISO       23
    SCK       SCK          18      SCK        18
    GPIO1/CS  CS            5      CS          5
    ACK       HANDSHAKE    33      Busy       33
    RESET     RESET        EN      Reset      EN
    GPIO0     DATAREADY     0      GP0         0
    TX        TX            1      TX          1
    RX        TX            3      RX          3
    RTS       MOSI/RTS     12      -          14
    CTS       CTS          33      -          33
    ========  ========== ========  =======  =======

