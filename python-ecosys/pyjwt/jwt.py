import binascii
import hashlib
import hmac
import json
from time import time

# Optionally depend on https://github.com/dmazzella/ucryptography
try:
    # Try importing from ucryptography port.
    import cryptography
    from cryptography import hashes, ec, serialization, utils

    _ec_supported = True
except ImportError:
    # No cryptography library available, no EC256 support.
    _ec_supported = False


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


def _sig_der_to_jws(signed):
    """Accept a DER signature and convert to JSON Web Signature bytes.

    `cryptography` produces signatures encoded in DER ASN.1 binary format.
    JSON Web Algorithm instead encodes the signature as the point coordinates
    as bigendian byte strings concatenated.

    See https://datatracker.ietf.org/doc/html/rfc7518#section-3.4
    """
    r, s = utils.decode_dss_signature(signed)
    return r.to_bytes(32, "big") + s.to_bytes(32, "big")


def _sig_jws_to_der(signed):
    """Accept a JSON Web Signature and convert to a DER signature.

    See `_sig_der_to_jws()`
    """
    r, s = int.from_bytes(signed[0:32], "big"), int.from_bytes(signed[32:], "big")
    return utils.encode_dss_signature(r, s)


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
    if algorithm != "HS256" and algorithm != "ES256":
        raise exceptions.InvalidAlgorithmError

    header = _to_b64url(json.dumps({"typ": "JWT", "alg": algorithm}).encode())
    payload = _to_b64url(json.dumps(payload).encode())

    if algorithm == "HS256":
        if isinstance(key, str):
            key = key.encode()
        signature = _to_b64url(hmac.new(key, header + b"." + payload, hashlib.sha256).digest())
    elif algorithm == "ES256":
        if not _ec_supported:
            raise exceptions.InvalidAlgorithmError(
                "Required dependencies for ES256 are not available"
            )
        if isinstance(key, int):
            key = ec.derive_private_key(key, ec.SECP256R1())
        signature = _to_b64url(
            _sig_der_to_jws(key.sign(header + b"." + payload, ec.ECDSA(hashes.SHA256())))
        )

    return (header + b"." + payload + b"." + signature).decode()


def decode(token, key, algorithms=["HS256", "ES256"]):
    if "HS256" not in algorithms and "ES256" not in algorithms:
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

    if header["alg"] not in algorithms or (header["alg"] != "HS256" and header["alg"] != "ES256"):
        raise exceptions.InvalidAlgorithmError

    if header["alg"] == "HS256":
        if isinstance(key, str):
            key = key.encode()
        calculated_signature = hmac.new(key, parts[0] + b"." + parts[1], hashlib.sha256).digest()
        if signature != calculated_signature:
            raise exceptions.InvalidSignatureError
    elif header["alg"] == "ES256":
        if not _ec_supported:
            raise exceptions.InvalidAlgorithmError(
                "Required dependencies for ES256 are not available"
            )

        if isinstance(key, bytes):
            key = ec.EllipticCurvePublicKey.from_encoded_point(key, ec.SECP256R1())
        try:
            key.verify(
                _sig_jws_to_der(signature),
                parts[0] + b"." + parts[1],
                ec.ECDSA(hashes.SHA256()),
            )
        except cryptography.exceptions.InvalidSignature:
            raise exceptions.InvalidSignatureError

    if "exp" in payload:
        if time() > payload["exp"]:
            raise exceptions.ExpiredSignatureError

    return payload
