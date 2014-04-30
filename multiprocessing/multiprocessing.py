import os


class Process:

    def __init__(self, group=None, target=None, name=None, args=(), kwargs={}):
        self.target = target
        self.args = args
        self.pid = 0

    def start(self):
        self.pid = os.fork()
        if not self.pid:
            self.target(*self.args)
            os._exit(0)
        else:
            return

    def join(self):
        os.waitpid(self.pid, 0)
