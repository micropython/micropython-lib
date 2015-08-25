import itertools

assert list(itertools.islice(list(range(10)), 4)) == [0, 1, 2, 3]
assert list(itertools.islice(list(range(10)), 2, 6)) == [2, 3, 4, 5]
assert list(itertools.islice(list(range(10)), 2, 6, 2)) == [2, 4]
