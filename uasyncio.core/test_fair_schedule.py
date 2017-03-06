# Test that uasyncio scheduling is fair, i.e. gives all
# coroutines equal chance to run (this specifically checks
# round-robin scheduling).
import uasyncio.core as asyncio


COROS = 5
ITERS = 5


result = []


async def coro(n):
    for i in range(ITERS):
        result.append(n)
        yield


async def done():
    while True:
        if len(result) == COROS * ITERS:
            #print(result)
            assert result == list(range(COROS)) * ITERS
            return
        yield


loop = asyncio.get_event_loop()

for n in range(COROS):
    loop.create_task(coro(n))

loop.run_until_complete(done())
