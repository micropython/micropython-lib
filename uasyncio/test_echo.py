from uasyncio import get_event_loop, open_connection, start_server, sleep_ms
from unittest import main, TestCase

class EchoTestCase(TestCase):

    def test_client_server(self):
        '''Simple client-server echo test'''
        sockaddr = ('127.0.0.1', 8080)
        l = get_event_loop()

        async def echo_server(reader, writer):
            data = await reader.readline()
            await writer.awrite(data)
            await writer.aclose()

        async def echo_client(line, result):
            await sleep_ms(10)  # Allow server to get up
            reader, writer = await open_connection(*sockaddr)
            await writer.awrite(line)
            data = await reader.readline()
            await writer.aclose()
            result.append(data)  # capture response

        result = []
        l.create_task(start_server(echo_server, *sockaddr))
        l.run_until_complete(echo_client(b'Hello\r\n', result))

        self.assertEqual(result[0], b'Hello\r\n')


if __name__ == '__main__':
    main()
