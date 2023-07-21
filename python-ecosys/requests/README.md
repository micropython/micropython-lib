## requests

This module provides a lightweight version of the Python
[requests](https://requests.readthedocs.io/en/latest/) library.

It includes support for all HTTP verbs, https, json decoding of responses,
redirects, basic authentication.

### Limitations

* Certificate validation is not currently supported.
* A dictionary passed as post data will not do automatic JSON or
  multipart-form encoding of post data (this can be done manually).
* Compressed requests/responses are not currently supported.
* File upload is not supported.
* Chunked encoding in responses is not supported.
