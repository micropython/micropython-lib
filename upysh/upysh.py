import sys
import os

class LS:

    def __repr__(self):
        l = os.listdir()
        l.sort()
        return "\n".join(l)

    def __call__(self, path="."):
        l = os.listdir(path)
        l.sort()
        for f in l:
            print(f)

class PWD:

    def __repr__(self):
        return os.getcwd()

    def __call__(self):
        return self.__repr__()

pwd = PWD()
ls = LS()

def cd(path):
    os.chdir(path)

def head(f, n=10):
    with open(f) as f:
        for i in range(n):
            l = f.readline()
            if not l: break
            sys.stdout.write(l)

def cat(f):
    head(f, 1 << 30)

def help():
    print("""
This is 'upysh' help, for builtin Python help run:
import builtins
builtins.help()

upysh commands:
pwd, cd("new_dir"), ls, ls(...), head(...), cat(...)
""")
