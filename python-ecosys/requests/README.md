## requests

This module provides a lightweight version of the Python
[requests](https://requests.readthedocs.io/en/latest/) library.

It includes support for all HTTP verbs, https, json decoding of responses,
redirects, basic authentication, HTTP/1.1 requests, and reading response
bodies with Content-Length or Transfer-Encoding: chunked via streaming
``.raw`` or lazy ``.content``.

### Limitations

* Certificates are not validated unless an ``ssl`` context is passed (see below).
* A dictionary passed as post data will not do automatic JSON or
  multipart-form encoding of post data (this can be done manually).
* Compressed requests/responses are not currently supported.
* File upload is not supported.
* HTTP keep-alive connection reuse is not supported (Connection: close by default).

### Verifying certificates

By default HTTPS requests accept any server certificate. To verify the
certificate chain and the hostname, pass an ``SSLContext`` as ``ssl``:

```py
import tls, requests

ctx = tls.SSLContext(tls.PROTOCOL_TLS_CLIENT)
ctx.verify_mode = tls.CERT_REQUIRED
ctx.load_verify_locations(root_der)
requests.get("https://example.com", ssl=ctx)
```

The context is used for redirects too.

### Follow-up work

* ``stream=True`` incremental body reads (see issue #777).
