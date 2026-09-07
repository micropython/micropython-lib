from functools import lru_cache, cache


@lru_cache(maxsize=8)
def f8(i):
    global count
    count += 1
    return i


count = 0
for i in range(8):
    assert f8(i) == i
assert count == 8
for i in range(8):
    assert f8(i) == i
assert count == 8

assert f8(100) == 100
assert count == 9
assert f8(5) == 5
assert count == 9
assert f8(0) == 0
assert count == 10


@lru_cache
def fdefault(i):
    global count
    count += 1
    return i


count = 0
for i in range(150):
    assert fdefault(i) == i
assert count == 150
for i in range(149, -1, -1):
    assert fdefault(i) == i
assert count == 150 + (150 - 128)


@lru_cache(maxsize=0)
def f0(i):
    global count
    count += 1
    return i


count = 0
for i in range(150):
    assert f0(i) == i
assert count == 150
for i in range(150):
    assert f0(i) == i
assert count == 300


@lru_cache(maxsize=None)
def fnone(i):
    global count
    count += 1
    return i


count = 0
for i in range(150):
    assert fnone(i) == i
assert count == 150
for i in range(150):
    assert fnone(i) == i
assert count == 150


@lru_cache
def fretnone(i):
    global count
    count += 1


count = 0
for i in range(150):
    assert fretnone(i) is None
assert count == 150
for i in range(149, -1, -1):
    assert fretnone(i) is None
assert count == 150 + (150 - 128)


@lru_cache
def fargs(i, i2):
    global count
    count += 1
    return i


count = 0
for i in range(150):
    assert fargs(i, i) == i
assert count == 150
for i in range(149, -1, -1):
    assert fargs(i, i) == i
assert count == 150 + (150 - 128)
for i in range(150):
    assert fargs(i, 10000) == i
assert count == 150 + (150 - 128) + 150


@lru_cache
def fvarargs(i, *args):
    global count
    count += 1
    return i


count = 0
for i in range(150):
    if i & 1 == 0:
        assert fvarargs(i) == i
    else:
        assert fvarargs(i, 'micropython') == i
assert count == 150
for i in range(149, -1, -1):
    if i & 1 == 0:
        assert fvarargs(i) == i
    else:
        assert fvarargs(i, 'micropython') == i
assert count == 150 + (150 - 128)
for i in range(150):
    assert fvarargs(i, 'micropython', 'more micropython') == i
assert count == 150 + (150 - 128) + 150


@lru_cache
def fkwargs(i, i2=None, i3=0, i4="a"):
    global count
    count += 1
    return i


count = 0
for i in range(150):
    assert fkwargs(i, i3=i) == i
assert count == 150
for i in range(149, -1, -1):
    assert fkwargs(i, i3=i) == i
assert count == 150 + (150 - 128)
for i in range(150):
    assert fkwargs(i, i3=10000) == i
assert count == 150 + (150 - 128) + 150


@cache
def fcache(i):
    global count
    count += 1
    return i


count = 0
for i in range(150):
    assert fcache(i) == i
assert count == 150
for i in range(150):
    assert fcache(i) == i
assert count == 150
