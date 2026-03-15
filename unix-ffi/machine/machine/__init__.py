from umachine import *
from .timer import *
from .pin import *


def unique_id():
    for base in ("/etc", "/var/lib/dbus"):
        try:
            with open(base + "/machine-id", "rb") as source:
                data = source.read(32)
                if len(data) == 32:
                    # unhexlify might not be available
                    return bytes([int(data[i : i + 2], 16) for i in range(0, 32, 2)])
        except OSError as e:
            pass
    return b"upy-non-unique"
