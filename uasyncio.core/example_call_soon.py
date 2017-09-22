import uasyncio.core as asyncio
import time


def cb():
    print("callback")
    time.sleep(0.5)
    loop.call_soon(cb)


loop = asyncio.get_event_loop()
loop.call_soon(cb)
loop.run_forever()
