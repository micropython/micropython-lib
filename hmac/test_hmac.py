import hmac
from hashlib.sha256 import sha256
from hashlib.sha512 import sha512

msg = b'zlutoucky kun upel dabelske ody'

dig = hmac.new(b'1234567890', msg=msg, digestmod=sha256).hexdigest()

print('c735e751e36b08fb01e25794bdb15e7289b82aecdb652c8f4f72f307b39dad39')
print(dig)

if dig != 'c735e751e36b08fb01e25794bdb15e7289b82aecdb652c8f4f72f307b39dad39':
    raise Exception("Error")

dig = hmac.new(b'1234567890', msg=msg, digestmod=sha512).hexdigest()

print('59942f31b6f5473fb4eb630fabf5358a49bc11d24ebc83b114b4af30d6ef47ea14b673f478586f520a0b9c53b27c8f8dd618c165ef586195bd4e98293d34df1a')
print(dig)

if dig != '59942f31b6f5473fb4eb630fabf5358a49bc11d24ebc83b114b4af30d6ef47ea14b673f478586f520a0b9c53b27c8f8dd618c165ef586195bd4e98293d34df1a':
    raise Exception("Error")

