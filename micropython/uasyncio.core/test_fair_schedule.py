# Test that uasyncio scheduling is fair, i.e. gives all
# coroutines equal chance to run (this specifically checks
# round-robin scheduling).
import uasyncio.core as asyncio


COROS = 10
ITERS = 20


result = []
test_finished = False


async def coro(n):
    for i in range(ITERS):
        result.append(n)
        yield


async def done():
    global test_finished
    while True:
        if len(result) == COROS * ITERS:
            #print(result)
            assert result == list(range(COROS)) * ITERS
            test_finished = True
            return
        yield


loop = asyncio.get_event_loop()

for n in range(COROS):
    loop.create_task(coro(n))

loop.run_until_complete(done())

assert test_finished
