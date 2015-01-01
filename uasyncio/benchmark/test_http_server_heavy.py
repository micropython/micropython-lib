import uasyncio as asyncio
import signal
import errno


cnt = 0

@asyncio.coroutine
def serve(reader, writer):
    global cnt
    #s = "Hello.\r\n"
    s = "Hello. %07d\r\n" % cnt
    cnt += 1
    yield from reader.read()
    yield from writer.awrite("HTTP/1.0 200 OK\r\n\r\n")
    try:
        yield from writer.awrite(s)
        yield from writer.awrite(s * 100)
        yield from writer.awrite(s * 400000)
        yield from writer.awrite("=== END ===")
        yield from writer.aclose()
    except OSError as e:
        if e.args[0] == errno.EPIPE:
            print("EPIPE")
        elif e.args[0] == errno.ECONNRESET:
            print("ECONNRESET")
        else:
            raise


import logging
logging.basicConfig(level=logging.INFO)
#logging.basicConfig(level=logging.DEBUG)
signal.signal(signal.SIGPIPE, signal.SIG_IGN)
loop = asyncio.get_event_loop()
mem_info()
loop.call_soon(asyncio.start_server(serve, "0.0.0.0", 8081, backlog=100))
loop.run_forever()
loop.close()
