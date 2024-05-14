import sys

# ruff: noqa: E402
sys.path.insert(0, ".")
import aiohttp
import asyncio


headers = {"Authorization": "Basic bG9naW46cGFzcw=="}


async def main():
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get("http://httpbin.org/headers") as r:
            json_body = await r.json()
            print(json_body)


asyncio.run(main())
