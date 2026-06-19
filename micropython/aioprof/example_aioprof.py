import time
import uasyncio as asyncio
import aioprof

aioprof.enable()


async def quicker():
    while True:
        time.sleep_ms(1)  # blocking sleep, shouldn't do this in asyncio.
        await asyncio.sleep_ms(20)


async def slow():
    while True:
        time.sleep_ms(80)  # long blocking sleep, _really_ shouldn't do this in asyncio!
        await asyncio.sleep_ms(20)


async def main():
    asyncio.create_task(slow())
    asyncio.create_task(quicker())

    await asyncio.sleep_ms(500)

    # print(aioprof.json())
    aioprof.report()


asyncio.run(main())
