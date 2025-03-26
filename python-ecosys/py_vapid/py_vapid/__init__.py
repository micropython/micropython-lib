"""
Based on https://github.com/web-push-libs/vapid
"""

import binascii
import time
import jwt

from cryptography import serialization


def _to_b64url(data):
    return (
        binascii.b2a_base64(data)
        .rstrip(b"\n")
        .rstrip(b"=")
        .replace(b"+", b"-")
        .replace(b"/", b"_")
    )


class Vapid:
    def __init__(self, private_key):
        self._private_key = private_key

    def sign(self, claims):
        claim = claims
        if "exp" not in claim:
            # Default to expiring 24 hours into the future (the max).
            # https://datatracker.ietf.org/doc/html/rfc8292#section-2
            exp = int(time.time()) + 86400
            # Correct the epoch offset if not the Unix standard.
            if time.gmtime(0)[0] == 2000:
                exp += 946684800  # Unix timestamp of 2000-01-01

            claim["exp"] = exp

        token = jwt.encode(claim, self._private_key, "ES256")
        public_key = _to_b64url(
            self._private_key.public_key().public_bytes(
                encoding=serialization.Encoding.X962,
                format=serialization.PublicFormat.UncompressedPoint,
            )
        ).decode()

        return {"Authorization": f"vapid t={token},k={public_key}"}


# Re-export for interface compatibility with PyPi py-vapid
Vapid02 = Vapid
