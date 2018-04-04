try:
    import uasyncio.core as asyncio
except ImportError:
    import asyncio
import logging

async def async_func_int(value:int) -> int:
    return value

async def async_func_int_sleep(value:int) -> int:
    await asyncio.sleep(1)
    return value

async def async_func_none() -> None:
    pass

async def async_func_none_sleep() -> None:
    await asyncio.sleep(1)


loop = asyncio.get_event_loop()
assert loop.run_until_complete(async_func_int(0)) == 0
assert loop.run_until_complete(async_func_int(-1)) == -1
assert loop.run_until_complete(async_func_int_sleep(-2)) == -2
assert loop.run_until_complete(async_func_none()) is None
assert loop.run_until_complete(async_func_none_sleep()) is None
