import uaiohttpclient as aiohttp
import asyncio


async def fetch(client):
    async with client.get("http://micropython.org") as resp:
        assert resp.status == 200
        return await resp.text()


async def main():
    async with aiohttp.ClientSession() as client:
        html = await fetch(client)
        print(html.decode())


if __name__ == "__main__":
    asyncio.run(main())
