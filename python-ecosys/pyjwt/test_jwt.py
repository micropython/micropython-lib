import jwt
from time import time

"""
Run tests by executing:

```
mpremote fs cp jwt.py :lib/jwt.py + run test_jwt.py
```

Only the full test suite can be run if
[ucryptography](https://github.com/dmazzella/ucryptography) is present in the
firmware.
"""

# Indentation
I = "    "

print("Testing HS256")
secret_key = "top-secret!"

token = jwt.encode({"user": "joe"}, secret_key, algorithm="HS256")
decoded = jwt.decode(token, secret_key, algorithms=["HS256"])
if decoded != {"user": "joe"}:
    raise Exception("Invalid decoded JWT")
else:
    print(I, "Encode/decode test: OK")

try:
    decoded = jwt.decode(token, "wrong-secret", algorithms=["HS256"])
except jwt.exceptions.InvalidSignatureError:
    print(I, "Invalid signature test: OK")
else:
    raise Exception("Invalid JWT should have failed decoding")

token = jwt.encode({"user": "joe", "exp": time() - 1}, secret_key)
try:
    decoded = jwt.decode(token, secret_key, algorithms=["HS256"])
except jwt.exceptions.ExpiredSignatureError:
    print(I, "Expired token test: OK")
else:
    raise Exception("Expired JWT should have failed decoding")


print("Testing ES256")
try:
    from cryptography import ec
except ImportError:
    raise Exception("No cryptography lib present, can't test ES256")

private_key = ec.derive_private_key(
    0xEB6DFB26C7A3C23D33C60F7C7BA61B6893451F2643E0737B20759E457825EE75, ec.SECP256R1()
)
wrong_private_key = ec.derive_private_key(
    0x25D91A0DA38F69283A0CE32B87D82817CA4E134A1693BE6083C2292BF562A451, ec.SECP256R1()
)

token = jwt.encode({"user": "joe"}, private_key, algorithm="ES256")
decoded = jwt.decode(token, private_key.public_key(), algorithms=["ES256"])
if decoded != {"user": "joe"}:
    raise Exception("Invalid decoded JWT")
else:
    print(I, "Encode/decode test: OK")

token = jwt.encode({"user": "joe"}, private_key, algorithm="ES256")
try:
    decoded = jwt.decode(token + "a", wrong_private_key.public_key(), algorithms=["ES256"])
except jwt.exceptions.InvalidSignatureError:
    print(I, "Invalid signature test: OK")
else:
    raise Exception("Invalid JWT should have fialed decoding")
