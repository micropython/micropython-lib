# aioespnow module for MicroPython on ESP32 and ESP8266
# MIT license; Copyright (c) 2022 Glenn Moloney @glenn20

import uasyncio as asyncio
import espnow


# Modelled on the uasyncio.Stream class (extmod/stream/stream.py)
# NOTE: Relies on internal implementation of uasyncio.core (_io_queue)
class AIOESPNow(espnow.ESPNow):
    # Read one ESPNow message
    async def arecv(self):
        yield asyncio.core._io_queue.queue_read(self)
        return self.recv(0)  # type: ignore[misc]

    async def airecv(self):
        yield asyncio.core._io_queue.queue_read(self)
        return self.irecv(0)  # type: ignore[misc]

    async def asend(self, mac, msg=None, sync=None):
        if msg is None:
            msg, mac = mac, None  # If msg is None: swap mac and msg
        yield asyncio.core._io_queue.queue_write(self)
        return self.send(mac, msg, sync)  # type: ignore[misc]

    # "async for" support
    def __aiter__(self):
        return self

    async def __anext__(self):
        return await self.airecv()
