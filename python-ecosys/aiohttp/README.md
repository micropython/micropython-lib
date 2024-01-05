aiohttp is an HTTP client module for MicroPython asyncio module,
with API mostly compatible with CPython [aiohttp](https://github.com/aio-libs/aiohttp)
module.

> [!NOTE]
> Only client is implemented.

See `examples/client.py`
```py
import aiohttp
import asyncio

async def main():

    async with aiohttp.ClientSession() as session:
        async with session.get('http://micropython.org') as response:

            print("Status:", response.status)
            print("Content-Type:", response.headers['Content-Type'])

            html = await response.text()
            print("Body:", html[:15], "...")

asyncio.run(main())
```
```
$ micropython examples/client.py
Status: 200
Content-Type: text/html; charset=utf-8
Body: <!DOCTYPE html> ...

```
