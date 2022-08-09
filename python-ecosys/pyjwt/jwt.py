import binascii
import hashlib
import hmac
import json
from time import time


def _to_b64url(data):
    return (
        binascii.b2a_base64(data)
        .rstrip(b"\n")
        .rstrip(b"=")
        .replace(b"+", b"-")
        .replace(b"/", b"_")
    )


def _from_b64url(data):
    return binascii.a2b_base64(data.replace(b"-", b"+").replace(b"_", b"/") + b"===")


class exceptions:
    class PyJWTError(Exception):
        pass

    class InvalidTokenError(PyJWTError):
        pass

    class InvalidAlgorithmError(PyJWTError):
        pass

    class InvalidSignatureError(PyJWTError):
        pass

    class ExpiredSignatureError(PyJWTError):
        pass


def encode(payload, key, algorithm="HS256"):
    if algorithm != "HS256":
        raise exceptions.InvalidAlgorithmError

    if isinstance(key, str):
        key = key.encode()
    header = _to_b64url(json.dumps({"typ": "JWT", "alg": algorithm}).encode())
    payload = _to_b64url(json.dumps(payload).encode())
    signature = _to_b64url(hmac.new(key, header + b"." + payload, hashlib.sha256).digest())
    return (header + b"." + payload + b"." + signature).decode()


def decode(token, key, algorithms=["HS256"]):
    if "HS256" not in algorithms:
        raise exceptions.InvalidAlgorithmError

    parts = token.encode().split(b".")
    if len(parts) != 3:
        raise exceptions.InvalidTokenError

    try:
        header = json.loads(_from_b64url(parts[0]).decode())
        payload = json.loads(_from_b64url(parts[1]).decode())
        signature = _from_b64url(parts[2])
    except Exception:
        raise exceptions.InvalidTokenError

    if header["alg"] not in algorithms or header["alg"] != "HS256":
        raise exceptions.InvalidAlgorithmError

    if isinstance(key, str):
        key = key.encode()
    calculated_signature = hmac.new(key, parts[0] + b"." + parts[1], hashlib.sha256).digest()
    if signature != calculated_signature:
        raise exceptions.InvalidSignatureError

    if "exp" in payload:
        if time() > payload["exp"]:
            raise exceptions.ExpiredSignatureError

    return payload
