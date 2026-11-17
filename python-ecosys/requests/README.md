## requests

This module provides a lightweight version of the Python
[requests](https://requests.readthedocs.io/en/latest/) library.

It includes support for all HTTP verbs, https, json decoding of responses,
redirects, basic authentication, HTTP/1.1 requests, and reading response
bodies with Content-Length or Transfer-Encoding: chunked via streaming
``.raw`` or lazy ``.content``.

### Limitations

* Certificates are only verified when an ``ssl`` context set to ``CERT_REQUIRED``
  is passed (see below).
* A dictionary passed as post data will not do automatic JSON or
  multipart-form encoding of post data (this can be done manually).
* Compressed requests/responses are not currently supported.
* File upload is not supported.
* HTTP keep-alive connection reuse is not supported (Connection: close by default).

### Verifying certificates

By default HTTPS requests accept any server certificate. To verify the
certificate chain and the hostname, pass an ``SSLContext`` whose
``verify_mode`` is ``CERT_REQUIRED`` as ``ssl``:

```py
import ssl, requests

ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
ctx.verify_mode = ssl.CERT_REQUIRED
ctx.load_verify_locations(cafile="ca.der")
with requests.get("https://example.com", ssl=ctx) as r:
    print(r.status_code)
```

* ``ca.der`` holds the root CA certificate the server's chain ends at: a
  single DER certificate, or one or more in PEM. The server must send any
  intermediate certificates.
* ``ssl.SSLContext`` starts with ``CERT_NONE``, and on mbedTLS ports
  ``CERT_OPTIONAL`` doesn't verify either, so set ``CERT_REQUIRED``.
* The device's clock must be set, for example with ``ntptime``, or
  certificates fail their validity check.
* A certificate that fails verification raises ``ValueError`` (``OSError``
  in rare cases), so catch both when retrying.
* With ``ssl`` given, an ``http://`` URL, or a redirect to one, raises
  ``ValueError`` instead of sending the request unencrypted. Redirects to
  ``https://`` are verified with the same context.
* Verification needs a port whose ``tls`` module uses mbedTLS. esp8266's
  axTLS can't verify certificates.
* Firmware that freezes ``requests`` uses the frozen copy ahead of one
  installed in ``/lib``.

### Follow-up work

* Verifying certificates by default, which needs a source of root
  certificates on the device (see issue #838).
* ``stream=True`` incremental body reads (see issue #777).
