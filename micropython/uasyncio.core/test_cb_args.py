try:
    import uasyncio.core as asyncio
except:
    import asyncio


def cb(a, b):
    assert a == "test"
    assert b == "test2"
    loop.stop()


loop = asyncio.get_event_loop()
loop.call_soon(cb, "test", "test2")
loop.run_forever()
print("OK")
