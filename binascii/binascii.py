from ubinascii import hexlify

def unhexlify(data):
    if len(data) % 2 != 0:
        raise Exception("Odd-length string")

    return b''.join([ int(data[i:i+2], 16).to_bytes(1) for i in range(0, len(data), 2) ])

b2a_hex = hexlify
a2b_hex = unhexlify

def b2a_base64():
    raise NotImplementError

def a2b_base64():
    raise NotImplementError
