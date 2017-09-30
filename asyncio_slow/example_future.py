#https://docs.python.org/3.4/library/asyncio-task.html#example-chain-coroutines
#import asyncio
import asyncio_slow as asyncio

@asyncio.coroutine
def slow_operation(future):
    yield from asyncio.sleep(1)
    future.set_result('Future is done!')

loop = asyncio.get_event_loop()
future = asyncio.Future()
asyncio.Task(slow_operation(future))
loop.run_until_complete(future)
print(future.result())
loop.close()
