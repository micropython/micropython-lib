import itertools

print(list(itertools.islice(list(range(10)), 4)))
print(list(itertools.islice(list(range(10)), 2, 6)))
print(list(itertools.islice(list(range(10)), 2, 6, 2)))
