# MicroPython aiohttp library
# MIT license; Copyright (c) 2023 Carlos Gil

import asyncio
import json as _json
from .aiohttp_ws import (
    _WSRequestContextManager,
    ClientWebSocketResponse,
    WebSocketClient,
    WSMsgType,
)

HttpVersion10 = "HTTP/1.0"
HttpVersion11 = "HTTP/1.1"


class ClientResponse:
    def __init__(self, reader):
        self.content = reader

    def _decode(self, data):
        c_encoding = self.headers.get("Content-Encoding")
        if c_encoding in ("gzip", "deflate", "gzip,deflate"):
            try:
                import deflate
                import io

                if c_encoding == "deflate":
                    with deflate.DeflateIO(io.BytesIO(data), deflate.ZLIB) as d:
                        return d.read()
                elif c_encoding == "gzip":
                    with deflate.DeflateIO(io.BytesIO(data), deflate.GZIP, 15) as d:
                        return d.read()
            except ImportError:
                print("WARNING: deflate module required")
        return data

    async def read(self, sz=-1):
        return self._decode(await self.content.read(sz))

    async def text(self, encoding="utf-8"):
        return (await self.read(int(self.headers.get("Content-Length", -1)))).decode(encoding)

    async def json(self):
        return _json.loads(await self.read(int(self.headers.get("Content-Length", -1))))

    def __repr__(self):
        return "<ClientResponse %d %s>" % (self.status, self.headers)


class ChunkedClientResponse(ClientResponse):
    def __init__(self, reader):
        self.content = reader
        self.chunk_size = 0

    async def read(self, sz=4 * 1024 * 1024):
        if self.chunk_size == 0:
            l = await self.content.readline()
            l = l.split(b";", 1)[0]
            self.chunk_size = int(l, 16)
            if self.chunk_size == 0:
                # End of message
                sep = await self.content.read(2)
                assert sep == b"\r\n"
                return b""
        data = await self.content.read(min(sz, self.chunk_size))
        self.chunk_size -= len(data)
        if self.chunk_size == 0:
            sep = await self.content.read(2)
            assert sep == b"\r\n"
        return self._decode(data)

    def __repr__(self):
        return "<ChunkedClientResponse %d %s>" % (self.status, self.headers)


class _RequestContextManager:
    def __init__(self, client, request_co):
        self.reqco = request_co
        self.client = client

    async def __aenter__(self):
        return await self.reqco

    async def __aexit__(self, *args):
        await self.client._reader.aclose()
        return await asyncio.sleep(0)


class ClientSession:
    def __init__(self, base_url="", headers={}, version=HttpVersion10):
        self._reader = None
        self._base_url = base_url
        self._base_headers = {"Connection": "close", "User-Agent": "compat"}
        self._base_headers.update(**headers)
        self._http_version = version

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return await asyncio.sleep(0)

    # TODO: Implement timeouts

    async def _request(self, method, url, data=None, json=None, ssl=None, params=None, headers={}):
        redir_cnt = 0
        while redir_cnt < 2:
            reader = await self.request_raw(method, url, data, json, ssl, params, headers)
            _headers = []
            sline = await reader.readline()
            sline = sline.split(None, 2)
            status = int(sline[1])
            chunked = False
            while True:
                line = await reader.readline()
                if not line or line == b"\r\n":
                    break
                _headers.append(line)
                if line.startswith(b"Transfer-Encoding:"):
                    if b"chunked" in line:
                        chunked = True
                elif line.startswith(b"Location:"):
                    url = line.rstrip().split(None, 1)[1].decode()

            if 301 <= status <= 303:
                redir_cnt += 1
                await reader.aclose()
                continue
            break

        if chunked:
            resp = ChunkedClientResponse(reader)
        else:
            resp = ClientResponse(reader)
        resp.status = status
        resp.headers = _headers
        resp.url = url
        if params:
            resp.url += "?" + "&".join(f"{k}={params[k]}" for k in sorted(params))
        try:
            resp.headers = {
                val.split(":", 1)[0]: val.split(":", 1)[-1].strip()
                for val in [hed.decode().strip() for hed in _headers]
            }
        except Exception:
            pass
        self._reader = reader
        return resp

    async def request_raw(
        self,
        method,
        url,
        data=None,
        json=None,
        ssl=None,
        params=None,
        headers={},
        is_handshake=False,
        version=None,
    ):
        if json and isinstance(json, dict):
            data = _json.dumps(json)
        if data is not None and method == "GET":
            method = "POST"
        if params:
            url += "?" + "&".join(f"{k}={params[k]}" for k in sorted(params))
        try:
            proto, dummy, host, path = url.split("/", 3)
        except ValueError:
            proto, dummy, host = url.split("/", 2)
            path = ""

        if proto == "http:":
            port = 80
        elif proto == "https:":
            port = 443
            if ssl is None:
                ssl = True
        else:
            raise ValueError("Unsupported protocol: " + proto)

        if ":" in host:
            host, port = host.split(":", 1)
            port = int(port)

        reader, writer = await asyncio.open_connection(host, port, ssl=ssl)

        # Use protocol 1.0, because 1.1 always allows to use chunked transfer-encoding
        # But explicitly set Connection: close, even though this should be default for 1.0,
        # because some servers misbehave w/o it.
        if version is None:
            version = self._http_version
        if "Host" not in headers:
            headers.update(Host=host)
        if not data:
            query = b"%s /%s %s\r\n%s\r\n" % (
                method,
                path,
                version,
                "\r\n".join(f"{k}: {v}" for k, v in headers.items()) + "\r\n" if headers else "",
            )
        else:
            if json:
                headers.update(**{"Content-Type": "application/json"})
            if isinstance(data, bytes):
                headers.update(**{"Content-Type": "application/octet-stream"})
            else:
                data = data.encode()

            headers.update(**{"Content-Length": len(data)})
            query = b"""%s /%s %s\r\n%s\r\n%s""" % (
                method,
                path,
                version,
                "\r\n".join(f"{k}: {v}" for k, v in headers.items()) + "\r\n",
                data,
            )
        if not is_handshake:
            await writer.awrite(query)
            return reader
        else:
            await writer.awrite(query)
            return reader, writer

    def request(self, method, url, data=None, json=None, ssl=None, params=None, headers={}):
        return _RequestContextManager(
            self,
            self._request(
                method,
                self._base_url + url,
                data=data,
                json=json,
                ssl=ssl,
                params=params,
                headers=dict(**self._base_headers, **headers),
            ),
        )

    def get(self, url, **kwargs):
        return self.request("GET", url, **kwargs)

    def post(self, url, **kwargs):
        return self.request("POST", url, **kwargs)

    def put(self, url, **kwargs):
        return self.request("PUT", url, **kwargs)

    def patch(self, url, **kwargs):
        return self.request("PATCH", url, **kwargs)

    def delete(self, url, **kwargs):
        return self.request("DELETE", url, **kwargs)

    def head(self, url, **kwargs):
        return self.request("HEAD", url, **kwargs)

    def options(self, url, **kwargs):
        return self.request("OPTIONS", url, **kwargs)

    def ws_connect(self, url, ssl=None):
        return _WSRequestContextManager(self, self._ws_connect(url, ssl=ssl))

    async def _ws_connect(self, url, ssl=None):
        ws_client = WebSocketClient(None)
        await ws_client.connect(url, ssl=ssl, handshake_request=self.request_raw)
        self._reader = ws_client.reader
        return ClientWebSocketResponse(ws_client)
