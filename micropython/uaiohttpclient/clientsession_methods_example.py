import uaiohttpclient as aiohttp
import asyncio


async def main():
    async with aiohttp.ClientSession("http://httpbin.org") as session:
        async with session.get("/get") as resp:
            assert resp.status == 200
            rget = await resp.text()
            print(f"GET: {rget.decode()}")
        async with session.post("/post", json={"foo": "bar"}) as resp:
            assert resp.status == 200
            rpost = await resp.text()
            print(f"POST: {rpost.decode()}")
        async with session.put("/put", data=b"data") as resp:
            assert resp.status == 200
            rput = await resp.json()
            print("PUT: ", rput)


if __name__ == "__main__":
    asyncio.run(main())
