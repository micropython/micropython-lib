try:
    import uasyncio as asyncio
except:
    import asyncio

try:
    import utime as time
except:
    import time

done = False

async def receiver():
    global done
    with open('./test_stream_read.py', 'rb') as f:
        sreader = asyncio.StreamReader(f)
        while True:
            await asyncio.sleep(0.1)
            res = await sreader.readline()
            done = True  # Never gets here


async def foo():
    start = time.time()
    while time.time() - start < 1.0:
        await asyncio.sleep(0)
    loop.stop()

loop = asyncio.get_event_loop()
loop.create_task(foo())
loop.create_task(receiver())
loop.run_forever()
assert done
print('OK')

