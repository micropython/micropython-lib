import itertools

assert list(itertools.islice(list(range(10)), 4)) == [0, 1, 2, 3]
assert list(itertools.islice(list(range(10)), 2, 6)) == [2, 3, 4, 5]
assert list(itertools.islice(list(range(10)), 2, 6, 2)) == [2, 4]

def g():
    while True:
        yield 123

assert list(itertools.islice(g(), 5)) == [123, 123, 123, 123, 123]

assert list(itertools.islice(itertools.cycle([1, 2, 3]), 10)) == [1, 2, 3, 1, 2, 3, 1, 2, 3, 1]
assert list(itertools.islice(itertools.cycle(reversed([1, 2, 3])), 7)) == [3, 2, 1, 3, 2, 1, 3]
