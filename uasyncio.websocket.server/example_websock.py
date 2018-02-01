import uasyncio
from uasyncio.websocket.server import WSReader, WSWriter


def echo(reader, writer):
    # Consume GET line
    yield from reader.readline()

    reader = yield from WSReader(reader, writer)
    writer = WSWriter(reader, writer)

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
loop.create_task(uasyncio.start_server(echo, "127.0.0.1", 8081))
loop.run_forever()
loop.close()
