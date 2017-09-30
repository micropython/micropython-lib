#import asyncio
import asyncio_slow as asyncio

@asyncio.coroutine
def greet_every_two_seconds():
    while True:
        print('Hello World')
        yield from asyncio.sleep(2)

loop = asyncio.get_event_loop()
asyncio.Task(greet_every_two_seconds())
loop.run_forever()
