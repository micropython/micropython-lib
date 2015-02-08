from ubinascii import hexlify

def unhexlify(data):
    chunks = [ data[i:i+2] for i in range(0, len(data), 2) ]
    return b''.join(map(lambda x: int(x, 16).to_bytes(1), chunks))

b2a_hex = hexlify
a2b_hex = unhexlify

def b2a_base64():
    raise NotImplementError

def a2b_base64():
    raise NotImplementError
