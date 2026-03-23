from collections import defaultdict

d = defaultdict.defaultdict(lambda: 42)
assert d[1] == 42
d[2] = 3
assert d[2] == 3
del d[1]
assert d[1] == 42

assert "foo" not in d

d = defaultdict.defaultdict(list)
for k, v in [('a', 1), ('b', 2), ('c', 3), ('a', 4), ('b', 5), ('c', 6)]:
    d[k].append(v)
i = list(sorted(d.items()))
assert i[0] == ('a', [1, 4])
assert i[1] == ('b', [2, 5])
assert i[2] == ('c', [3, 6])
