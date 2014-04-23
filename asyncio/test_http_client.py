import asyncio

@asyncio.coroutine
def print_http_headers(url):
    reader, writer = yield from asyncio.open_connection(url, 80)
    print(reader, writer)
    print("================")
    query = "GET / HTTP/1.0\r\nHost: foo\r\n\r\n"
#    query = "GET / HTTP/1.0\r\n\r\n"
    print(query.encode('latin-1'))
    yield from writer.write(query)
    while True:
        line = yield from reader.readline()
#        1/0
        if not line:
            break
        if line:
            print(line)

url = "google.com"
loop = asyncio.get_event_loop()
#task = asyncio.async(print_http_headers(url))
#loop.run_until_complete(task)
loop.call_soon(print_http_headers(url))
loop.run_forever()
loop.close()
