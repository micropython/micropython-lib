import uasyncio
import uasyncio_.websocket


def echo(reader, writer):
    while 1:
        l = yield from reader.read(256)
        print(l)
        if l == b"\r":
            await writer.awrite(b"\r\n")
        else:
            await writer.awrite(l)


import logging
#logging.basicConfig(level=logging.INFO)
logging.basicConfig(level=logging.DEBUG)
loop = uasyncio.get_event_loop()
#loop.create_task(asyncio.start_server(serve, "127.0.0.1", 8081))
loop.create_task(uasyncio_.websocket.start_ws_server(echo, "127.0.0.1", 8081))
loop.run_forever()
loop.close()
