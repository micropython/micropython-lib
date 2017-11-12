from random import *


UPPER = 100

s = set()

for c in range(650):
    r = randrange(UPPER)
    s.add(r)

assert len(s) == UPPER
