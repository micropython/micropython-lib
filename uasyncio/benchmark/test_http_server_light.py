import uasyncio as asyncio


@asyncio.coroutine
def serve(reader, writer):
    #print(reader, writer)
    #print("================")
    yield from reader.read()
    yield from writer.awrite("HTTP/1.0 200 OK\r\n\r\nHello.\r\n")
    yield from writer.close()
    #print("Finished processing request")


import logging
#logging.basicConfig(level=logging.INFO)
logging.basicConfig(level=logging.DEBUG)
loop = asyncio.get_event_loop()
mem_info()
loop.call_soon(asyncio.start_server(serve, "127.0.0.1", 8081, backlog=100))
loop.run_forever()
loop.close()
