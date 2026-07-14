# Python itertools adapted for Micropython by rkompass (2022)
# Largely, but not exclusively based on code from the offical Python documentation
#    (https://docs.python.org/3/library/itertools.html)
# Copyright 2001-2019 Python Software Foundation; All Rights Reserved

# consumes about 5kB if imported

# accumulate([1,2,3,4,5]) --> 1 3 6 10 15
# accumulate([1,2,3,4,5], initial=100) --> 100 101 103 106 110 115
# accumulate([1,2,3,4,5], lambda x, y: x * y) --> 1 2 6 24 120
def accumulate(iterable, func=lambda x, y: x + y, initial=None):
    it = iter(iterable)
    total = initial
    if initial is None:
        try:
            total = next(it)
        except StopIteration:
            return
    yield total
    for element in it:
        total = func(total, element)
        yield total


# chain('abcd',[],range(5))) --> 'a' 'b' 'c' 'd' 0 1 2 3 4
class chain:
    def __init__(self, *iterables):
        self.iterables = list(iterables)
        self.it = iter([])

    def __iter__(self):
        return self

    def __next__(self):
        while True:
            try:
                return next(self.it)
            except StopIteration:
                try:
                    self.it = iter(self.iterables.pop(0))
                    continue
                except IndexError:
                    raise StopIteration

    # chain.from_iterable(['ABC', 'DEF']) --> 'A' 'B' 'C' 'D' 'E' 'F'
    @staticmethod
    def from_iterable(iterables):
        for it in iterables:
            yield from it


# combinations('ABCD', 2) --> ('A','B') ('A','C') ('A','D') ('B','C') ('B','D') ('C','D')
def combinations(iterable, r):
    pool = tuple(iterable)
    n = len(pool)
    if r > n:
        return
    indices = list(range(r))
    yield tuple(pool[i] for i in indices)
    while True:
        index = 0
        for i in reversed(range(r)):
            if indices[i] != i + n - r:
                index = i
                break
        else:
            return
        indices[index] += 1
        for j in range(index + 1, r):
            indices[j] = indices[j - 1] + 1
        yield tuple(pool[i] for i in indices)


# combinations_with_replacement('ABC', 2) --> ('A','A') ('A','B') ('A','C') ('B','B') ('B','C') ('C','C')
def combinations_with_replacement(iterable, r):
    pool = tuple(iterable)
    n = len(pool)
    if not n and r:
        return
    indices = [0] * r
    yield tuple(pool[i] for i in indices)
    while True:
        index = 0
        for i in reversed(range(r)):
            if indices[i] != n - 1:
                index = i
                break
        else:
            return
        indices[index:] = [indices[index] + 1] * (r - index)
        yield tuple(pool[i] for i in indices)


# compress('ABCDEF', [1,0,1,0,1,1]) --> A C E F
def compress(data, selectors):
    return (d for d, s in zip(data, selectors) if s)


# count(4, 3) --> 4 7 10 13 16 19 ....
def count(start=0, step=1):
    while True:
        yield start
        start += step


# cycle('abc') --> a b c a b c a b c a ....
def cycle(iterable):
    try:
        len(iterable)
    except TypeError:  # len() not defined: Assume p is a finite iterable: We cache the elements.
        cache = []
        for i in iterable:
            yield i
            cache.append(i)
        iterable = cache
    while iterable:
        yield from iterable


# # dropwhile(lambda x: x<5, [1,4,6,4,1]) --> 6 4 1
def dropwhile(predicate, iterable):
    it = iter(iterable)
    for x in it:
        if not predicate(x):
            yield x
            break
    for x in it:
        yield x


# filterfalse(lambda x: x%2, range(10)) --> 0 2 4 6 8
def filterfalse(predicate, iterable):
    if predicate is None:
        predicate = bool
    for x in iterable:
        if not predicate(x):
            yield x


# groupby('aaaabbbccdaa'))) --> ('a', gen1) ('b', gen2) ('c', gen3) ('d', gen4) ('a', gen5)
#                       where gen1 --> a a a a, gen2 --> b b b, gen3 --> c c, gen4 --> d, gen5 --> a a
def groupby(iterable, key=None):
    it = iter(iterable)
    keyf = key if key is not None else lambda x: x

    def ggen(ktgt):
        nonlocal cur, kcur
        while kcur == ktgt:
            yield cur
            try:
                cur = next(it)
                kcur = keyf(cur)
            except StopIteration:
                break

    kcur = kold = object()  # need an object that never can be a returned from key function
    while True:
        while (
            kcur == kold
        ):  # not all iterables with the same (old) key were used up by ggen, so use them up here
            try:
                cur = next(it)
                kcur = keyf(cur)
            except StopIteration:
                return
        kold = kcur
        yield (kcur, ggen(kcur))


# islice('abcdefghij', 2, None, 3)) --> c f i
# islice(range(10), 2, 6, 2)) --> 2 4
def islice(iterable, *sargs):
    if len(sargs) < 1 or len(sargs) > 3:
        raise TypeError(
            "islice expected at least 2, at most 4 arguments, got {:d}".format(len(sargs) + 1)
        )
    step = 1 if len(sargs) < 3 else sargs[2]
    step = 1 if step is None else step
    if step <= 0:
        raise ValueError("step for islice() must be a positive integer or None")
    start = 0 if len(sargs) < 2 else sargs[0]
    stop = sargs[0] if len(sargs) == 1 else sargs[1]
    it = iter(iterable)
    try:
        for i in range(start):
            next(it)
        while True:
            if stop is not None and start >= stop:
                return
            yield next(it)
            for i in range(step - 1):
                next(it)
            start += step
    except StopIteration:
        return


# pairwise(range(5)) --> (0,1) (1,2) (2,3) (3,4)
# pairwise('abcdefg') --> ('a','b') ('b','c') ('c','d') ('d','e') ('e','f') ('f','g')
def pairwise(iterable):
    it = iter(iterable)
    try:
        l = next(it)
        while True:
            c = next(it)
            yield l, c
            l = c
    except StopIteration:
        return


# permutations('ABCD', 2) --> AB AC AD BA BC BD CA CB CD DA DB DC
# permutations(range(3)) --> 012 021 102 120 201 210
def permutations(iterable, r=None):
    pool = tuple(iterable)
    n = len(pool)
    r = n if r is None else r
    if r > n:
        return
    indices = list(range(n))
    cycles = list(range(n, n - r, -1))
    yield tuple(pool[i] for i in indices[:r])
    while n:
        for i in reversed(range(r)):
            cycles[i] -= 1
            if cycles[i] == 0:
                indices[i:] = indices[i + 1 :] + indices[i : i + 1]
                cycles[i] = n - i
            else:
                j = cycles[i]
                indices[i], indices[-j] = indices[-j], indices[i]
                yield tuple(pool[i] for i in indices[:r])
                break
        else:
            return


# product('ABCD', 'xy') --> ('A','x') ('A','y') ('B','x') ('B','y') ('C','x') ('C','y') ('D','x') ('D','y')
# product(range(2), repeat=3) --> 000 001 010 011 100 101 110 111  # but in tuples, of course
def product(*args, repeat=1):
    pools = [tuple(pool) for pool in args] * repeat
    result = [[]]
    for pool in pools:
        result = [x + [y] for x in result for y in pool]
    for prod in result:
        yield tuple(prod)


# repeat(10, 3) --> 10 10 10
def repeat(obj, times=None):
    if times is None:
        while True:
            yield obj
    else:
        for _ in range(times):
            yield obj


# starmap(pow, [(2,5), (3,2), (10,3)]) --> 32 9 1000
def starmap(function, iterable):
    for args in iterable:
        yield function(*args)


# takewhile(lambda x: x<5, [1,4,6,4,1]) --> 1 4
def takewhile(predicate, iterable):
    for x in iterable:
        if predicate(x):
            yield x
        else:
            break


# tee(range(2,10), 3) --> (it1, it2, it3) all parallel generators, but dependent on original generator (e.g. range(2,10))
#  --> (min(it1), max(it2), sum(it3)) --> (2, 9, 44)
def tee(iterable, n=2):
    if iter(iterable) is not iter(
        iterable
    ):  # save buffer for special cases that iterable is range, tuple, list ...
        return [iter(iterable) for _ in range(n)]  #   that have independent iterators
    it = iter(iterable)
    if n < 1:
        return ()
    elif n == 1:
        return (it,)
    buf = []  # Buffer, contains stored values from itr
    ibuf = [0] * n  # Indices of the individual generators, could be array('H', [0]*n)

    def gen(k):  #   but we have no 0 in ibuf in MP
        nonlocal buf, ibuf  # These are bound to the generators as closures
        while True:
            if ibuf[k] < len(buf):  # We get an object stored in the buffer.
                r = buf[ibuf[k]]
                ibuf[k] += 1
                if ibuf[k] == 1:  # If we got the first object in the buffer,
                    if 0 not in ibuf:  #   then check if other generators do not wait anymore on it
                        buf.pop(
                            0
                        )  #   so it may be popped left. Afterwards decrease all indices by 1.
                        for i in range(n):
                            ibuf[i] -= 1
            elif ibuf[k] == len(buf):
                try:
                    r = next(it)
                    buf.append(r)
                    ibuf[k] += 1
                except StopIteration:
                    return
            yield r  # The returned generators are not thread-safe. For that the access to the

    return tuple(gen(i) for i in range(n))  #   shared buf and ibuf should be protected by locks.


# zip_longest('ABCD', 'xy', fillvalue='-') --> ('A','x') ('B','y') ('C','-') ('D','-')
def zip_longest(*args, fillvalue=None):
    iterators = [iter(it) for it in args]
    num_active = len(iterators)
    if not num_active:
        return
    while True:
        values = []
        for i, it in enumerate(iterators):
            try:
                value = next(it)
            except StopIteration:
                num_active -= 1
                if not num_active:
                    return
                iterators[i] = repeat(fillvalue)
                value = fillvalue
            values.append(value)
        yield tuple(values)


# # Full analog of CPython builtin iter with 2 arguments
# def iter(*args):
#
#     if len(args) == 1:
#         return builtins.iter(args[0])
#
#     class _iter:
#
#         def __init__(self, args):
#             self.f, self.sentinel = args
#         def __next__(self):
#             v = self.f()
#             if v == self.sentinel:
#                 raise StopIteration
#             return v
#
#     return _iter(args)
