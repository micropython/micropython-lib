# type: ignore
class ABC:
    pass


def abstractmethod(arg):
    return arg

try:
    # add functionality if typing module is available
    from typing import __getattr__ as __getattr__

except: # naked except saves 4 bytes
    pass
