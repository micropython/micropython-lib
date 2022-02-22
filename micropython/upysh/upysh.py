import sys
import os


class LS:
    def __repr__(self):
        self.__call__()
        return ""

    def __call__(self, path="."):
        l = list(os.ilistdir(path))
        l.sort()
        for f in l:
            if f[1] == 0x4000:  # stat.S_IFDIR
                print("    <dir> %s" % f[0])
        for f in l:
            if f[1] != 0x4000:
                if len(f) > 3:
                    print("% 9d %s" % (f[3], f[0]))
                else:
                    print("          %s" % f[0])
        try:
            st = os.statvfs(path)
            print("\n{:,d}k free".format(st[1] * st[3] // 1024))
        except:
            pass


class PWD:
    def __repr__(self):
        return os.getcwd()

    def __call__(self):
        return self.__repr__()


class CLEAR:
    def __repr__(self):
        return "\x1b[2J\x1b[H"

    def __call__(self):
        return self.__repr__()


def head(f, n=10):
    with open(f) as f:
        for i in range(n):
            l = f.readline()
            if not l:
                break
            sys.stdout.write(l)


def cat(f):
    head(f, 1 << 30)


def cp(s, t):
    try:
        if os.stat(t)[0] & 0x4000:  # is directory
            t = t.rstrip("/") + "/" + s
    except OSError:
        pass
    buf = bytearray(512)
    buf_mv = memoryview(buf)
    with open(s, "rb") as s, open(t, "wb") as t:
        while True:
            n = s.readinto(buf)
            if n <= 0:
                break
            t.write(buf_mv[:n])


def newfile(path):
    print("Type file contents line by line, finish with EOF (Ctrl+D).")
    with open(path, "w") as f:
        while 1:
            try:
                l = input()
            except EOFError:
                break
            f.write(l)
            f.write("\n")


def rm(d, recursive=False):  # Remove file or tree
    try:
        if (os.stat(d)[0] & 0x4000) and recursive:  # Dir
            for f in os.ilistdir(d):
                if f[0] != "." and f[0] != "..":
                    rm("/".join((d, f[0])))  # File or Dir
            os.rmdir(d)
        else:  # File
            os.remove(d)
    except:
        print("rm of '%s' failed" % d)


class Man:
    def __repr__(self):
        return """
upysh is intended to be imported using:
from upysh import *

To see this help text again, type "man".

upysh commands:
clear, ls, ls(...), head(...), cat(...), newfile(...)
cp('src', 'dest'), mv('old', 'new'), rm(...)
pwd, cd(...), mkdir(...), rmdir(...)
"""


man = Man()
pwd = PWD()
ls = LS()
clear = CLEAR()

cd = os.chdir
mkdir = os.mkdir
mv = os.rename
rmdir = os.rmdir

print(man)
