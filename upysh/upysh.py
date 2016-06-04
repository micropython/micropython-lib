import sys
import os

class LS:

    def __repr__(self):
        self.__call__()
        return ""

    def __call__(self, path="."):
        l = os.listdir(path)
        l.sort()
        for f in l:
            st = os.stat("%s/%s" % (path, f))
            if st[0] & 0x4000:  # stat.S_IFDIR
                print("   <dir> %s" % f)
            else:
                print("% 8d %s" % (st[6], f))

class PWD:

    def __repr__(self):
        res = os.getcwd()
        if res == "": # TLD on esp8266
            res = "/"
        return res

    def __call__(self):
        return self.__repr__()

class CLEAR:

    def __repr__(self):
        return "\x1b[2J\x1b[H"

    def __call__(self):
        return self.__repr__()
        
class HELP:

    def __repr__(self):
        return ("""
This is 'upysh' help. upysh commands:

cat(file)
clear 
cd("new_dir") 
ls 
ls(object) 
head(file [, #_of_lines]) 
help
mkdir(newdir) 
mv(from, to)
newfile(file)
pwd
rm(file)
rmdir(empty_dir)
""")

    def __call__(self):
        return self.__repr__()

        
pwd = PWD()
ls = LS()
clear = CLEAR()
help = HELP()
cd = os.chdir
mkdir = os.mkdir
mv = os.rename
rm = os.remove
rmdir = os.remove

def head(f, n=10):
    with open(f) as f:
        for i in range(n):
            l = f.readline()
            if not l: break
            sys.stdout.write(l)

def cat(f):
    head(f, 1 << 30)

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

