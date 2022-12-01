import itertools

# accumulate
assert list(itertools.accumulate([])) == []
assert list(itertools.accumulate([0])) == [0]
assert list(itertools.accumulate([0, 2, 3])) == [0, 2, 5]
assert list(itertools.accumulate(reversed([0, 2, 3]))) == [3, 5, 5]
assert list(itertools.accumulate([1, 2, 3], lambda x, y: x * y)) == [1, 2, 6]
assert list(itertools.accumulate([1,2,3,4,5], func=lambda x, y: x - y, initial=10)) == [10, 9, 7, 4, 0, -5]

# chain
assert list(itertools.chain()) == []
assert list(itertools.chain([],[],[])) == []
assert list(itertools.chain(range(3),[2*(i+1) for i in range(4)])) == [0, 1, 2, 2, 4, 6, 8]
assert list(itertools.chain('abcd',[],range(5))) == ['a', 'b', 'c', 'd', 0, 1, 2, 3, 4]

assert list(itertools.chain.from_iterable([])) == []
assert list(itertools.chain.from_iterable(['ABC', 'DEF'])) == ['A', 'B', 'C', 'D', 'E', 'F']

# combinations
assert list(itertools.combinations('', 1)) == []
assert list(itertools.combinations('ABCD', 0)) == [()]
assert list(itertools.combinations('ABCD', 1)) == [('A',), ('B',), ('C',), ('D',)]
assert list(itertools.combinations('ABCD', 3)) == [('A', 'B', 'C'), ('A', 'B', 'D'), ('A', 'C', 'D'), ('B', 'C', 'D')]
assert list(itertools.combinations('ABCD', 4)) == [('A', 'B', 'C', 'D')]
assert list(itertools.combinations('ABCD', 5)) == []
assert len(list(itertools.combinations(range(7), 4))) == 35
assert len(set(itertools.combinations(range(7), 4))) == 35

# combinations with replacement
assert list(itertools.combinations_with_replacement('ABCD', 0)) == [()]
assert list(itertools.combinations_with_replacement('ABCD', 1)) == [('A',), ('B',), ('C',), ('D',)]
assert list(itertools.combinations_with_replacement('ABC', 2)) == [('A', 'A'), ('A', 'B'), ('A', 'C'), ('B', 'B'), ('B', 'C'), ('C', 'C')]
assert list(itertools.combinations_with_replacement('ABC', 3)) == [('A', 'A', 'A'), ('A', 'A', 'B'), ('A', 'A', 'C'), ('A', 'B', 'B'), ('A', 'B', 'C'), ('A', 'C', 'C'), ('B', 'B', 'B'), ('B', 'B', 'C'), ('B', 'C', 'C'), ('C', 'C', 'C')]

# compress
assert tuple(itertools.compress('ABCDEF', (1,0,1,0,1,1))) == ('A', 'C', 'E', 'F')
assert tuple(itertools.compress('ABCDEF', (1,0,1,1,0))) == ('A', 'C', 'D')

# count
it = itertools.count(4, 3)
for _ in range(200):
    n = next(it)
assert list(next(it) for _ in range(5)) == [604, 607, 610, 613, 616]

# cycle
it = itertools.cycle(iter('abcde'))
assert list(next(it) for _ in range(12)) == ['a', 'b', 'c', 'd', 'e', 'a', 'b', 'c', 'd', 'e', 'a', 'b']
it = itertools.cycle([2, 4, 'x'])
assert list(next(it) for _ in range(7)) == [2, 4, 'x', 2, 4, 'x', 2]

# dropwhile
assert list(itertools.dropwhile(lambda x: x<5, [1,4,6,4,1])) == [6, 4, 1]
assert list(itertools.dropwhile(lambda x: ord(x)<118, '')) == []
assert list(itertools.dropwhile(lambda x: ord(x)<118, 'dropwhile')) == ['w', 'h', 'i', 'l', 'e']

# filterfalse
assert list(itertools.filterfalse(lambda x: ord(x)<110, 'dropwhile')) == ['r', 'o', 'p', 'w']

# groupby
assert list(((k,''.join(g)) for k,g in itertools.groupby('aaaabbbccdaa'))) == [('a', 'aaaa'), ('b', 'bbb'), ('c', 'cc'), ('d', 'd'), ('a', 'aa')]

# islice
assert ''.join(itertools.islice('', 2, 5)) == ''
assert ''.join(itertools.islice('abcdefgh', 2, 5)) == 'cde'
assert ''.join(itertools.islice('abcdefghij', 2, None, 3)) == 'cfi'
assert ''.join(itertools.islice('abcdefghij', 2, None)) == 'cdefghij'
assert ''.join(itertools.islice('abcdefghij', 6)) == 'abcdef'
assert ''.join(itertools.islice('abcdefghij', 6, 6)) == ''
assert list(itertools.islice(range(10), 2, 6, 2)) == [2, 4]
assert list(itertools.islice(itertools.cycle([1, 2, 3]), 10)) == [1, 2, 3, 1, 2, 3, 1, 2, 3, 1]

# pairwise
assert list(itertools.pairwise(range(5))) == [(0, 1), (1, 2), (2, 3), (3, 4)]
assert list((''.join(t) for t in itertools.pairwise('abcdefg'))) == ['ab', 'bc', 'cd', 'de', 'ef', 'fg']
assert list((''.join(t) for t in itertools.pairwise('ab'))) == ['ab']
assert list((''.join(t) for t in itertools.pairwise('a'))) == []
assert list((''.join(t) for t in itertools.pairwise(''))) == []

# permutations
assert list(itertools.permutations('', 1)) == []
assert list((''.join(t) for t in itertools.permutations('a', 2))) == []
assert list((''.join(t) for t in itertools.permutations('abcd', 0))) == ['']
assert list((''.join(t) for t in itertools.permutations('ab', 2))) == ['ab', 'ba']
assert list((''.join(t) for t in itertools.permutations('abcd', 2))) == ['ab', 'ac', 'ad', 'ba', 'bc', 'bd', 'ca', 'cb', 'cd', 'da', 'db', 'dc']
assert list(itertools.permutations(range(3))) == [(0, 1, 2), (0, 2, 1), (1, 0, 2), (1, 2, 0), (2, 0, 1), (2, 1, 0)]

# product
assert list(itertools.product()) == [()]
assert list(itertools.product(range(2), repeat=0)) == [()]
assert list((''.join(t) for t in itertools.product('ABC', 'xy'))) == ['Ax', 'Ay', 'Bx', 'By', 'Cx', 'Cy']
assert list((''.join(t) for t in itertools.product('A', 'xy', repeat=2))) == ['AxAx', 'AxAy', 'AyAx', 'AyAy']
assert list((''.join(map(str,t)) for t in itertools.product(range(2), repeat=3))) == ['000','001','010','011','100','101','110','111']

# repeat
assert list(itertools.repeat(10, 0)) == []
assert list(itertools.repeat(10, 1)) == [10]
assert list(itertools.repeat(10, 3)) == [10, 10, 10]

# starmap
assert list(itertools.starmap(pow, [])) == []
assert list(itertools.starmap(pow, [(2,5), (3,2), (10,3)])) == [32, 9, 1000]
assert list(itertools.starmap(lambda x, y: x * y, [[1, 2], [2, 3], [3, 4]])) == [2, 6, 12]

# takewhile
assert list(itertools.takewhile(lambda x: x<5, [1,4,6,4,1])) == [1, 4]
assert list(itertools.takewhile(lambda x: ord(x)<118, 'dropwhile')) == ['d', 'r', 'o', 'p']

# tee
def genx(n):
    i=1;
    while True:
        yield i; i+=1
        if i >n:
            return
it1, it2, it3 = itertools.tee(genx(1000), 3);  _ = next(it1)  # case of iterable that is unique; iterate once
assert [min(it1), max(it2), sum(it3)] == [2, 1000, 500500] 
it1, it2, it3 = itertools.tee(range(2,10), 3); _ = next(it1)  # iterable that is not unique; iterate once
assert [min(it1), max(it2), sum(it3)] == [3, 9, 44]           # the min is increased, other iterators remained full

# zip_longest
assert list(itertools.zip_longest('', '')) == []
assert list(itertools.zip_longest('', '', fillvalue='-')) == []
assert list(itertools.zip_longest('', 'xy')) == [(None, 'x'), (None, 'y')]
assert list(itertools.zip_longest('', 'xy', fillvalue='-')) == [('-', 'x'), ('-', 'y')]
assert list(itertools.zip_longest('ABCD', 'xy', fillvalue='-')) == [('A','x'),('B','y'),('C','-'),('D','-')]

