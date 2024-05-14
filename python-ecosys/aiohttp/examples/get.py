import sys

# ruff: noqa: E402
sys.path.insert(0, ".")
import aiohttp
import asyncio


URL = sys.argv.pop()

if not URL.startswith("http"):
    URL = "http://micropython.org"

print(URL)


async def fetch(client):
    async with client.get(URL) as resp:
        assert resp.status == 200
        return await resp.text()


async def main():
    async with aiohttp.ClientSession() as client:
        html = await fetch(client)
        print(html)


if __name__ == "__main__":
    asyncio.run(main())
