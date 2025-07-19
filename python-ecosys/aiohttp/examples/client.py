import sys

# ruff: noqa: E402
sys.path.insert(0, ".")
import aiohttp
import asyncio


async def main():
    async with aiohttp.ClientSession() as session:
        async with session.get("http://micropython.org") as response:
            print("Status:", response.status)
            print("Content-Type:", response.headers["Content-Type"])

            html = await response.text()
            print("Body:", html[:15], "...")


asyncio.run(main())
