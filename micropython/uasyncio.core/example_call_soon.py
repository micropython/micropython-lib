import uasyncio.core as asyncio
import time
import logging
logging.basicConfig(level=logging.DEBUG)
#asyncio.set_debug(True)


def cb():
    print("callback")
    time.sleep(0.5)
    loop.call_soon(cb)


loop = asyncio.get_event_loop()
loop.call_soon(cb)
loop.run_forever()
