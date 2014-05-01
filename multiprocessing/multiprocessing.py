import os
import pickle


class Process:

    def __init__(self, group=None, target=None, name=None, args=(), kwargs={}):
        self.target = target
        self.args = args
        self.kwargs = kwargs
        self.pid = 0
        self.r = self.w = None

    def start(self):
        self.pid = os.fork()
        if not self.pid:
            if self.r:
                self.r.close()
            self.target(*self.args, **self.kwargs)
            os._exit(0)
        else:
            if self.w:
                self.w.close()
            return

    def join(self):
        os.waitpid(self.pid, 0)

    def register_pipe(self, r, w):
        """Extension to CPython API: any pipe used for parent/child
        communication should be registered with this function."""
        self.r, self.w = r, w


class Connection:

    def __init__(self, fd):
        self.fd = fd
        self.f = open(fd)

    def __repr__(self):
        return "<Connection %s>" % self.f

    def send(self, obj):
        s = pickle.dumps(obj)
        self.f.write(len(s).to_bytes(4))
        self.f.write(s)

    def recv(self):
        s = self.f.read(4)
        l = int.from_bytes(s)
        s = self.f.read(l)
        return pickle.loads(s)

    def close(self):
        self.f.close()


def Pipe(duplex=True):
    assert duplex == False
    r, w = os.pipe()
    return Connection(r), Connection(w)


class Pool:

    def __init__(self, num):
        self.num = num

    def apply(self, f, args=(), kwargs={}):
        # This is pretty inefficient impl, doesn't really use pool worker
        def _exec(w):
            r = f(*args, **kwargs)
            w.send(r)
        r, w = Pipe(False)
        p = Process(target=_exec, args=(w,))
        p.register_pipe(r, w)
        p.start()
        r = r.recv()
        p.join()
        return r
