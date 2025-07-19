#
# uaiohttpclient - fetch URL passed as command line argument.
#
import sys
import asyncio
import uaiohttpclient as aiohttp


async def run(url):
    resp = await aiohttp.request("GET", url)
    print(resp)
    print(await resp.read())


url = sys.argv[1]
asyncio.run(run(url))
