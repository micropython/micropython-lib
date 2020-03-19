try:
    import uasyncio.core as asyncio
    from uasyncio.synchro import Lock
except ImportError:
    import asyncio
    from asyncio import Lock


def task(i, lock):
    print(lock)
    while 1:
        yield from lock.acquire()
        print("Acquired lock in task", i)
        yield from asyncio.sleep(0.5)
#        yield lock.release()
        lock.release()


loop = asyncio.get_event_loop()

lock = Lock()

loop.create_task(task(1, lock))
loop.create_task(task(2, lock))
loop.create_task(task(3, lock))

loop.run_forever()
