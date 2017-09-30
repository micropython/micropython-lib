#https://docs.python.org/3.4/library/asyncio-task.html#example-hello-world-coroutine
#import asyncio
import asyncio_slow as asyncio

@asyncio.coroutine
def greet_every_two_seconds():
    while True:
        print('Hello World')
        yield from asyncio.sleep(2)

loop = asyncio.get_event_loop()
loop.run_until_complete(greet_every_two_seconds())
