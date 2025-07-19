import sys

# ruff: noqa: E402
sys.path.insert(0, ".")
import aiohttp
import asyncio


params = {"key1": "value1", "key2": "value2"}


async def main():
    async with aiohttp.ClientSession() as session:
        async with session.get("http://httpbin.org/get", params=params) as response:
            expect = "http://httpbin.org/get?key1=value1&key2=value2"
            assert str(response.url) == expect, f"{response.url} != {expect}"
            html = await response.text()
            print(html)


asyncio.run(main())
