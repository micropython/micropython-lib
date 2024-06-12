# `aioespnow`

A supplementary module which extends the micropython `espnow` module to provide
`asyncio` support.

- Asyncio support is available on all ESP32 targets as well as those ESP8266
boards which include the `asyncio` module (ie. ESP8266 devices with at least
2MB flash storage).

## API reference

- class `AIOESPNow()`: inherits all the methods of the `ESPNow` class and
  extends the interface with the following async methods:

  - `async AIOESPNow.arecv()`

      Asyncio support for ESPNow.recv(). Note that this method does not take a
      timeout value as argument.

  - `async AIOESPNow.airecv()`

      Asyncio support for ESPNow.irecv(). Use this method to reduce memory
      fragmentation, as it will reuse common storage for each new message
      received, whereas the `arecv()` method will allocate new memory for every
      message received.

  - `async AIOESPNow.asend(mac, msg, sync=True)`
  - `async AIOESPNow.asend(msg)`

      Asyncio support for ESPNow.send().

  - `__aiter__()/async __anext__()`

      AIOESPNow also supports reading incoming messages by asynchronous
      iteration using `async for`, eg:

    ```python
      e = AIOESPNow()
      e.active(True)
      async def recv_till_halt(e):
          async for mac, msg in e:
              print(mac, msg)
              if msg == b'halt':
                  break
      asyncio.run(recv_till_halt(e))
    ```

## Example Usage

A small async server example::

```python
    import network
    import aioespnow
    import asyncio

    # A WLAN interface must be active to send()/recv()
    network.WLAN(network.STA_IF).active(True)

    e = aioespnow.AIOESPNow()  # Returns AIOESPNow enhanced with async support
    e.active(True)
    peer = b'\xbb\xbb\xbb\xbb\xbb\xbb'
    e.add_peer(peer)

    # Send a periodic ping to a peer
    async def heartbeat(e, peer, period=30):
        while True:
            if not await e.asend(peer, b'ping'):
                print("Heartbeat: peer not responding:", peer)
            else:
                print("Heartbeat: ping", peer)
            await asyncio.sleep(period)

    # Echo any received messages back to the sender
    async def echo_server(e):
        async for mac, msg in e:
            print("Echo:", msg)
            try:
                await e.asend(mac, msg)
            except OSError as err:
                if len(err.args) > 1 and err.args[1] == 'ESP_ERR_ESPNOW_NOT_FOUND':
                    e.add_peer(mac)
                    await e.asend(mac, msg)

    async def main(e, peer, timeout, period):
        asyncio.create_task(heartbeat(e, peer, period))
        asyncio.create_task(echo_server(e))
        await asyncio.sleep(timeout)

    asyncio.run(main(e, peer, 120, 10))
```
