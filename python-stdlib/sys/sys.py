from usys import *


def intern(s):
    # MicroPython has its own interning mechanism so just return the string,
    # which might or might not actually be interned.
    return s
