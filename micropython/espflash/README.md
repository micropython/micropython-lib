Instructions on building the NINAW10 and esp_hosted firmware

# Building the NINAW10 firmware

The NINAW10 firmware only works with classic ESP32 devices. No support
for newer models like ESP32C3.

## Get the NINAW10 Arduino source code

The link is https://github.com/arduino/nina-fw.git.

## Get the ESP32 development environment.

Follow the instructions in the README.md document of the NINA firmware to
download the NINA firmware and the esp-idf.
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

    // for NINA W102:
    SPISClass SPIS(VSPI_HOST, 1, 12, 23, 18, 5, 33);

    // for Airlift:
    SPISClass SPIS(VSPI_HOST, 1, 14, 23, 18, 5, 33);


Change UART pins at about line 123 in this file: 

nina-fw-1.5.0-Arduino/main/sketch.ino.cpp

Suitable settings:

    // Airlift
    uart_set_pin(UART_NUM_1, 1, 3, 33, 14); // TX, RX, RTS, CTS

    // W102
    uart_set_pin(UART_NUM_1, 1, 3, 33, 12); // TX, RX, RTS, CTS

The respective pin assignments can be found below in the pin table.
The only difference between the Arduino Airlift and NINAW102 module
is for the RTS/MOSI pin. If you use a custom ESP32 device and want to
use different pins, you can change the pin numbers as needed.

## Build the firmware

Call `make RELEASE=1 NANO_RP2040_CONNECT=1` to build the firmware.
Run combine.py with `python combine.py` to get a combined firmware
file, which can be loaded to the target module using e.g. espflash.py.
The file name will be `NINA_W102.bin`.

# Building the esp-hosted firmware

The esp-hosted firmware should work with all ESP32 modules. Tested with
a ESP32 classic and a ESP32C3.

## Get the esp-hosted source code

The source code repository is at:

https://github.com/espressif/esp-hosted.git

The code for the esp-hosted network adapter is at:

esp_hosted_fg/esp/esp_driver

## Get the ESP32 development environment.

Follow the instructions in the README.md of micropython/ports/esp32.

./install.sh  
git submodule sync  
git submodule update --init

in the esp-idf directory.

## Check the SPI and UART pins.

The SPI pins are defined in the file:  

esp_hosted_fg/esp/esp_driver/network_adapter/main/spi_slave_api.c

The SPI settings used for the airlift module with ESP32 are:

    #define GPIO_MOSI          14
    #define GPIO_MISO          23
    #define GPIO_SCLK          18
    #define GPIO_CS            5

The UART pins for bluetooth are defined in the file:  

esp_hosted_fg/esp/esp_driver/network_adapter/main/slave_bt.h

The UART settings used for the airlift module with ESP32 are:

    #define BT_TX_PIN           1
    #define BT_RX_PIN           3
    #define BT_RTS_PIN         14
    #define BT_CTS_PIN         23

The respective pin assignments can be found ni the table below.
The only difference between the Arduino Airlift and NINAW102 module
is for the RTS/MOSI pin. If you use a custom ESP32 device and want to
use different pins, you can change the pin numbers as needed.

## Build the firmware

Build the firmware using:

idf.py build

Create the combined firmware with the script:

    #!/usr/bin/env python

    import sys;

    booloaderData = open("build/bootloader/bootloader.bin", "rb").read()
    partitionData = open("build/partition_table/partition-table.bin", "rb").read()
    otaData = open("build/ota_data_initial.bin", "rb").read()
    network_adapterData = open("build/network_adapter.bin", "rb").read()

    # calculate the output binary size, app offset
    outputSize = 0x10000 + len(network_adapterData)
    if (outputSize % 1024):
        outputSize += 1024 - (outputSize % 1024)

    # allocate and init to 0xff
    outputData = bytearray(b'\xff') * outputSize

    # copy data: bootloader, partitions, app
    for i in range(0, len(booloaderData)):
        outputData[0x1000 + i] = booloaderData[i]

    for i in range(0, len(partitionData)):
        outputData[0x8000 + i] = partitionData[i]

    for i in range(0, len(otaData)):
            outputData[0xd000 + i] = otaData[i]

    for i in range(0, len(network_adapterData)):
        outputData[0x10000 + i] = network_adapterData[i]

    outputFilename = "esp_hosted_airlift.bin"
    if (len(sys.argv) > 1):
        outputFilename = sys.argv[1]

    # write out
    with open(outputFilename,"w+b") as f:
        f.seek(0)
        f.write(outputData)

The combined firmware file will be `esp_hosted_airlift.bin`. This
file can be loaded to the target module using e.g. espflash.py.


# NINAW10 and esp-hosted pins assignments

Mapping between firmware signal names and ESP32 pins for the NINA
firmware and esp_hosted firmware

    ========  ========== ========  =======  =======
    NINAW10   esp_hosted   NINA    Airlift  Airlift
    Name      Name       W102 pin   Name      pin
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

