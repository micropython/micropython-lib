# -*- coding: utf-8 -*-
#
#   @file
#   @brief: Bluetooth Generic Attribute Service
#
# Copyright (c) 2021, Planet Innovation
# 436 Elgar Road, Box Hill, 3128, VIC, Australia
# Phone: +61 3 9945 7510
#
# The copyright to the computer program(s) herein is the property of
# Planet Innovation, Australia.
# The program(s) may be used and/or copied only with the written permission
# of Planet Innovation or in accordance with the terms and conditions
# stipulated in the agreement/contract under which the program(s) have been
# supplied.
#

import ustruct
import bluetooth
from aioble import Service, Characteristic, security
from aioble.core import ble, log_info
from hashlib import md5
from ubinascii import hexlify
try:
    from utyping import *
except:
    pass


class GenericAttributeService(Service):
    # Generic Attribute service UUID
    SERVICE_UUID = bluetooth.UUID(0x1801)

    # Service Changed Characteristic
    UUID_SERVICE_CHANGED = bluetooth.UUID(0x2A05)
    # Database Hash Characteristic (New in BLE 5.1)
    UUID_DATABASE_HASH = bluetooth.UUID(0x2B2A)

    def __init__(self, services: Tuple[Service]):

        super().__init__(self.SERVICE_UUID)

        # Database hash is typically a 128bit AES-CMAC value, however
        # is generally only monitored for change as an opaque value.
        # MD5 is also 128 bit, faster and builtin
        hasher = md5()
        for service in services:
            for char in service.characteristics:
                hasher.update(char.uuid)
                hasher.update(str(char.flags))
        self.digest = hasher.digest()
        self.hexdigest = hexlify(self.digest).decode()
        log_info("BLE: DB Hash=", self.hexdigest)
        security.current_digest = self.hexdigest
        security.gatt_svc = self

        self.SERVICE_CHANGED = Characteristic(
            service=self,
            uuid=self.UUID_SERVICE_CHANGED,
            read=True,
            indicate=True,
            initial=''
        )

        self.DATABASE_HASH = Characteristic(
            service=self,
            uuid=self.UUID_DATABASE_HASH,
            read=True,
            initial=self.digest
        )

    def send_changed(self, connection, start=0, end=0xFFFF):
        self.SERVICE_CHANGED.write(ustruct.pack('!HH', start, end))
        log_info("Indicate Service Changed")
        ble.gatts_indicate(connection._conn_handle, self.SERVICE_CHANGED._value_handle)
