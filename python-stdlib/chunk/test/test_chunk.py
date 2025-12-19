from chunk import Chunk
from micropython import const

logo = open("micropython-logo.tiff", "rb")

CHUNK_SIZE = const(23) # Arbitrary size

while True:
    try:
        chunk = Chunk(logo)
    except EOFError:
        break
    chunktype = chunk.getname()
    while True:
        data = chunk.read(CHUNK_SIZE)
        if not data:
            break
        print(data)
