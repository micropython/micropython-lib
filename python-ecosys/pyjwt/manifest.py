metadata(
    version="0.2.0",
    pypi="pyjwt",
    description="""
JWT library for MicroPython.  Supports HMAC (HS256) encoding essentially.
Optionally supports ECDSA (ES256) asymmetric-key signing/verification when the
[dmazella/ucryptography](https://github.com/dmazzella/ucryptography/) library
is available in the MicroPython firmware.
""",
)

require("hmac")

module("jwt.py")
