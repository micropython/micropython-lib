import sys

# ruff: noqa: E402
sys.path.insert(0, ".")
import aiohttp
import asyncio

headers = {"Accept-Encoding": "gzip,deflate"}


async def main():
    async with aiohttp.ClientSession(headers=headers, version=aiohttp.HttpVersion11) as session:
        async with session.get("http://micropython.org") as response:
            print("Status:", response.status)
            print("Content-Type:", response.headers["Content-Type"])
            print(response.headers)
            html = await response.text()
            print(html)


asyncio.run(main())
