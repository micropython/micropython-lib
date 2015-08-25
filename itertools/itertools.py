def count(start=0, step=1):
    while True:
        yield start
        start += step

def cycle(p):
    while p:
        yield from p

def repeat(el, n=None):
    if n is None:
        while True:
            yield el
    else:
        for i in range(n):
            yield el

def chain(*p):
    for i in p:
        yield from i

def islice(p, start, stop=(), step=1):
    if stop == ():
        stop = start
        start = 0
    while True:
        try:
            yield p[start]
        except IndexError:
            return
        start += step
        if start >= stop:
            return

def tee(iterable, n=2):
    return [iter(iterable)] * n
