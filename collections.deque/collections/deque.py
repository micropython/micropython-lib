class deque:

    def __init__(self, iterable=None):
        if iterable is None:
            self.q = []
        else:
            self.q = list(iterable)

    def popleft(self):
        return self.q.pop(0)

    def popright(self):
        return self.q.pop()

    def pop(self):
        return self.q.pop()

    def append(self, a):
        self.q.append(a)

    def appendleft(self, a):
        self.q = [a] + self.q

    def __len__(self):
        return len(self.q)

    def __bool__(self):
        return bool(self.q)
