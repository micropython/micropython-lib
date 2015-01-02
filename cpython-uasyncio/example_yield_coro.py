import uasyncio as asyncio


def run1():
    for i in range(1):
        print('Hello World')
        yield from asyncio.sleep(2)
    print("run1 finished")

def run2():
    for i in range(3):
        print('bar')
        yield run1()
        yield from asyncio.sleep(1)


import logging
logging.basicConfig(level=logging.INFO)
loop = asyncio.get_event_loop()
loop.create_task(run2())
loop.run_forever()
