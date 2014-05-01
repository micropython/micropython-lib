# https://docs.python.org/3.4/library/asyncio-eventloop.html#example-hello-world-callback
#import asyncio
import asyncio_slow as asyncio

def print_and_repeat(loop):
    print('Hello World')
    loop.call_later(2, print_and_repeat, loop)

loop = asyncio.get_event_loop()
loop.call_soon(print_and_repeat, loop)
loop.run_forever()
