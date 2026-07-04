## requests

This module provides a lightweight version of the Python
[requests](https://requests.readthedocs.io/en/latest/) library.

It includes support for all HTTP verbs, https, json decoding of responses,
redirects, basic authentication, HTTP/1.1 requests, and reading response
bodies with Content-Length or Transfer-Encoding: chunked via streaming
``.raw`` or lazy ``.content``.

### Limitations

* Certificate validation is not currently supported.
* A dictionary passed as post data will not do automatic JSON or
  multipart-form encoding of post data (this can be done manually).
* Compressed requests/responses are not currently supported.
* File upload is not supported.
* HTTP keep-alive connection reuse is not supported (Connection: close by default).

### Follow-up work

* TLS certificate verification (see micropython-lib issue #838).
* ``stream=True`` incremental body reads (see issue #777).
