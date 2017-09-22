import uasyncio as asyncio

@asyncio.coroutine
def serve(reader, writer):
    print(reader, writer)
    print("================")
    print((yield from reader.read()))
    yield from writer.awrite("HTTP/1.0 200 OK\r\n\r\nHello.\r\n")
    print("After response write")
    yield from writer.aclose()
    print("Finished processing request")


import logging
#logging.basicConfig(level=logging.INFO)
logging.basicConfig(level=logging.DEBUG)
loop = asyncio.get_event_loop()
loop.call_soon(asyncio.start_server(serve, "127.0.0.1", 8081))
loop.run_forever()
loop.close()
