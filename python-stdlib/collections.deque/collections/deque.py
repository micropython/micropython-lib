class deque:
    def __init__(self, iterable=None, maxlen=None):
        if iterable is None:
            self.q = []
        else:
            self.q = list(iterable)
        if maxlen is not None:
            if not isinstance(maxlen, int):
                raise TypeError("" "an integer is required")
            if maxlen < 0:
                raise ValueError("" "maxlen must be non-negative")
        self.__maxlen = maxlen

    def popleft(self):
        return self.q.pop(0)

    def pop(self):
        return self.q.pop()

    def append(self, a):
        self.q.append(a)
        if self.__maxlen is not None and len(self.q) > self.__maxlen:
            self.popleft()

    def appendleft(self, a):
        self.q.insert(0, a)
        if self.__maxlen is not None and len(self.q) > self.__maxlen:
            self.pop()

    def extend(self, a):
        if len(self.q) + len(a) > self.__maxlen:
            raise IndexError
        self.q.extend(a)

    def clear(self):
        self.q.clear()

    @property
    def maxlen(self):
        return self.__maxlen

    def __len__(self):
        return len(self.q)

    def __bool__(self):
        return bool(self.q)

    def __iter__(self):
        yield from self.q

    def __str__(self):
        return "deque({})".format(self.q)

    def __getitem__(self, idx):
        return self.q[idx]
