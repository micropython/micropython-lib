import ujwt
from time import time

secret_key = "top-secret!"

jwt = ujwt.encode({"user": "joe"}, secret_key)
decoded = ujwt.decode(jwt, secret_key)
if decoded != {"user": "joe"}:
    raise Exception("Invalid decoded JWT")
else:
    print("Encode/decode test: OK")

try:
    decoded = ujwt.decode(jwt, "wrong-secret")
except ujwt.exceptions.InvalidSignatureError:
    print("Invalid signature test: OK")
else:
    raise Exception("Invalid JWT should have failed decoding")

jwt = ujwt.encode({"user": "joe", "exp": time() - 1}, secret_key)
try:
    decoded = ujwt.decode(jwt, secret_key)
except ujwt.exceptions.ExpiredTokenError:
    print("Expired token test: OK")
else:
    raise Exception("Expired JWT should have failed decoding")
