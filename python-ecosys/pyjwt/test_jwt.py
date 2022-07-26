import jwt
from time import time

secret_key = "top-secret!"

token = jwt.encode({"user": "joe"}, secret_key, algorithm="HS256")
print(token)
decoded = jwt.decode(token, secret_key, algorithms=["HS256"])
if decoded != {"user": "joe"}:
    raise Exception("Invalid decoded JWT")
else:
    print("Encode/decode test: OK")

try:
    decoded = jwt.decode(token, "wrong-secret", algorithms=["HS256"])
except jwt.exceptions.InvalidSignatureError:
    print("Invalid signature test: OK")
else:
    raise Exception("Invalid JWT should have failed decoding")

token = jwt.encode({"user": "joe", "exp": time() - 1}, secret_key)
print(token)
try:
    decoded = jwt.decode(token, secret_key, algorithms=["HS256"])
except jwt.exceptions.ExpiredSignatureError:
    print("Expired token test: OK")
else:
    raise Exception("Expired JWT should have failed decoding")
