import sys

# ruff: noqa: E402
sys.path.insert(0, ".")
import aiohttp
import asyncio

try:
    URL = sys.argv[1]  # expects a websocket echo server
except Exception:
    URL = "ws://echo.websocket.events"


sslctx = False

if URL.startswith("wss:"):
    try:
        import ssl

        sslctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        sslctx.verify_mode = ssl.CERT_NONE
    except Exception:
        pass


async def ws_test_echo(session):
    async with session.ws_connect(URL, ssl=sslctx) as ws:
        await ws.send_str("hello world!\r\n")
        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                print(msg.data)

            if "close" in msg.data:
                break
            await ws.send_str("close\r\n")
        await ws.close()


async def main():
    async with aiohttp.ClientSession() as session:
        await ws_test_echo(session)


if __name__ == "__main__":
    asyncio.run(main())
