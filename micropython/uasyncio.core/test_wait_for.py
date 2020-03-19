try:
    import uasyncio.core as asyncio
except ImportError:
    import asyncio
import logging
#logging.basicConfig(level=logging.DEBUG)
#asyncio.set_debug(True)


def looper(iters):
    for i in range(iters):
        print("ping")
        yield from asyncio.sleep(1.0)
    return 10


def run_to():
    try:
        ret = yield from asyncio.wait_for(looper(2), 1)
        print("result:", ret)
        assert False
    except asyncio.TimeoutError:
        print("Coro timed out")

    print("=================")

    try:
        ret = yield from asyncio.wait_for(looper(2), 2)
        print("result:", ret)
        assert False
    except asyncio.TimeoutError:
        print("Coro timed out")

    print("=================")

    try:
        ret = yield from asyncio.wait_for(looper(2), 3)
        print("result:", ret)
    except asyncio.TimeoutError:
        print("Coro timed out")
        assert False


loop = asyncio.get_event_loop()
loop.run_until_complete(run_to())
loop.run_until_complete(asyncio.sleep(1))
