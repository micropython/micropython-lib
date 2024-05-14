import sys

# ruff: noqa: E402
sys.path.insert(0, ".")
import aiohttp
import asyncio

try:
    URL = sys.argv[1]  # expects a websocket echo server
    READ_BANNER = False
except Exception:
    URL = "ws://echo.websocket.events"
    READ_BANNER = True


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
        if READ_BANNER:
            print(await ws.receive_str())
        try:
            while True:
                await ws.send_str(f"{input('>>> ')}\r\n")

                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        print(msg.data, end="")
                        break

        except KeyboardInterrupt:
            pass

        finally:
            await ws.close()


async def main():
    async with aiohttp.ClientSession() as session:
        await ws_test_echo(session)


if __name__ == "__main__":
    asyncio.run(main())
