import sys
import os


class _Ls:
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


class _Pwd:
    def __repr__(self):
        return os.getcwd()

    def __call__(self):
        return self.__repr__()


class _Clear:
    def __repr__(self):
        return "\x1b[2J\x1b[H"

    def __call__(self):
        return self.__repr__()


class _StdinCommand:
    def __init__(self, command, args):
        self.command = command
        self.args = args.copy()

    def __repr__(self):
        cur_args = []
        for prompt, parser, default in self.args:
            arg = input(prompt + ": ")
            if arg == "":
                if default is not None:
                    arg = default
                else:
                    print(f"You must provide {prompt.lower()}")
                    return ""
            else:
                arg = parser(arg)

            cur_args.append(arg)

        self.command(*cur_args)
        return ""

    def __call__(self, *args):
        self.command(*args)


def _head_func(f, n=10):
    with open(f) as f:
        for i in range(n):
            l = f.readline()
            if not l:
                break
            sys.stdout.write(l)


def _cat_func(f):
    head(f, 1 << 30)


def _cp_func(s, t):
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


def _newfile_func(path):
    print("Type file contents line by line, finish with EOF (Ctrl+D).")
    with open(path, "w") as f:
        while 1:
            try:
                l = input()
            except EOFError:
                break
            f.write(l)
            f.write("\n")


def _rm_func(d, recursive=False):  # Remove file or tree
    try:
        if (os.stat(d)[0] & 0x4000) and recursive:  # Dir
            for f in os.ilistdir(d):
                if f[0] != "." and f[0] != "..":
                    rm("/".join((d, f[0])), True)  # File or Dir
            os.rmdir(d)
        else:  # File
            os.remove(d)
    except:
        print("rm of '%s' failed" % d)


class _Man:
    def __repr__(self):
        return """
upysh is intended to be imported using:
from upysh import *

To see this help text again, type "man".

upysh commands:
clear, ls, ls(...), head(...)*, cat(...)*, newfile(...)*
cp('src', 'dest')*, mv('old', 'new')*, rm(name, recursive=False)*
pwd, cd(...)*, mkdir(...)*, rmdir(...)*

Most commands (marked with *) can be called interactively.
It means you don't have to type tons of brackets and quotes
(something alike what you expect from a normal shell),
to figure out this behavior just type cd or mv
"""


man = _Man()
pwd = _Pwd()
ls = _Ls()
clear = _Clear()

head = _StdinCommand(_head_func, [["Filename", str, None], ["Num of lines (default=10)", int, 10]])

cat = _StdinCommand(_cat_func, [["Filename", str, None]])

cp = _StdinCommand(_cp_func, [["Source", str, None], ["Target", str, None]])

newfile = _StdinCommand(_newfile_func, [["Filename", str, None]])

rm = _StdinCommand(_rm_func, [["Filename", str, None], ["Recursive (default=False)", bool, False]])

cd = _StdinCommand(os.chdir, [["Target", str, None]])

mkdir = _StdinCommand(os.mkdir, [["Directory name", str, None]])

mv = _StdinCommand(os.rename, [["Source", str, None], ["Target", str, None]])

rmdir = _StdinCommand(os.rmdir, [["Directory name", str, None]])

print(man)
