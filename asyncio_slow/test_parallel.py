#https://docs.python.org/3.4/library/asyncio-task.html#example-parallel-execution-of-tasks
#import asyncio
import asyncio_slow as asyncio

@asyncio.coroutine
def factorial(name, number):
    f = 1
    for i in range(2, number+1):
        print("Task %s: Compute factorial(%s)..." % (name, i))
        yield from asyncio.sleep(1)
        f *= i
    print("Task %s: factorial(%s) = %s" % (name, number, f))

tasks = [
    asyncio.Task(factorial("A", 2)),
    asyncio.Task(factorial("B", 3)),
    asyncio.Task(factorial("C", 4))]

loop = asyncio.get_event_loop()
loop.run_until_complete(asyncio.wait(tasks))
loop.close()
