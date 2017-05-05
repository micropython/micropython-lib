#
# This script optimizes a Python source distribution tarball as produced by
# "python3 setup.py sdist" command for MicroPython's native package manager,
# upip. Optimization includes:
#  * Removing metadata files not used by upip (this includes setup.py)
#  * Recompressing gzip archive with 4K dictionary size so it can be
#    installed even on low-heap targets.
#
import sys
import os
import zlib
from subprocess import Popen, PIPE
import glob
import tarfile
import re
import io


def gzip_4k(inf, fname):
    comp = zlib.compressobj(level=9, wbits=16 + 12)
    with open(fname + ".out", "wb") as outf:
        while 1:
            data = inf.read(1024)
            if not data:
                break
            outf.write(comp.compress(data))
        outf.write(comp.flush())
    os.rename(fname, fname + ".orig")
    os.rename(fname + ".out", fname)


def recompress(fname):
    with Popen(["gzip", "-d", "-c", fname], stdout=PIPE).stdout as inf:
        gzip_4k(inf, fname)

def find_latest(dir):
    res = []
    for fname in glob.glob(dir + "/*.gz"):
        st = os.stat(fname)
        res.append((st.st_mtime, fname))
    res.sort()
    latest = res[-1][1]
    return latest


def recompress_latest(dir):
    latest = find_latest(dir)
    print(latest)
    recompress(latest)


FILTERS = [
    # include, exclude, repeat
    (r".+\.egg-info/(PKG-INFO|requires\.txt)", r"setup.py$"),
    (r".+\.py$", r"[^/]+$"),
    (None, r".+\.egg-info/.+"),
]


outbuf = io.BytesIO()

def filter_tar(name):
    fin = tarfile.open(name, "r:gz")
    fout = tarfile.open(fileobj=outbuf, mode="w")
    for info in fin:
#        print(info)
        if not "/" in info.name:
            continue
        fname = info.name.split("/", 1)[1]
        include = None

        for inc_re, exc_re in FILTERS:
            if include is None and inc_re:
                if re.match(inc_re, fname):
                    include = True

            if include is None and exc_re:
                if re.match(exc_re, fname):
                    include = False

        if include is None:
            include = True

        if include:
            print("Including:", fname)
        else:
            print("Excluding:", fname)
            continue

        farch = fin.extractfile(info)
        fout.addfile(info, farch)
    fout.close()
    fin.close()



from setuptools import Command

class OptimizeUpip(Command):

    user_options = []

    def run(self):
        latest = find_latest("dist")
        filter_tar(latest)
        outbuf.seek(0)
        gzip_4k(outbuf, latest)

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass


# For testing only
if __name__ == "__main__":
#    recompress_latest(sys.argv[1])
    filter_tar(sys.argv[1])
    outbuf.seek(0)
    gzip_4k(outbuf, sys.argv[1])
