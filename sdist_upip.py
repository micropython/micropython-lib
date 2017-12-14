#
# This module overrides distutils (also compatible with setuptools) "sdist"
# command to perform pre- and post-processing as required for MicroPython's
# upip package manager.
#
# Preprocessing steps:
#  * Creation of Python resource module (R.py) from each top-level package's
#    resources.
# Postprocessing steps:
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

from distutils.filelist import FileList
from setuptools.command.sdist import sdist as _sdist


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
            print("including:", fname)
        else:
            print("excluding:", fname)
            continue

        farch = fin.extractfile(info)
        fout.addfile(info, farch)
    fout.close()
    fin.close()


def make_resource_module(manifest_files):
        resources = []
        # Any non-python file included in manifest is resource
        for fname in manifest_files:
            ext = fname.rsplit(".", 1)[1]
            if ext != "py":
                resources.append(fname)

        if resources:
            print("creating resource module R.py")
            resources.sort()
            last_pkg = None
            r_file = None
            for fname in resources:
                try:
                    pkg, res_name = fname.split("/", 1)
                except ValueError:
                    print("not treating %s as a resource" % fname)
                    continue
                if last_pkg != pkg:
                    last_pkg = pkg
                    if r_file:
                        r_file.write("}\n")
                        r_file.close()
                    r_file = open(pkg + "/R.py", "w")
                    r_file.write("R = {\n")

                with open(fname, "rb") as f:
                    r_file.write("%r: %r,\n" % (res_name, f.read()))

            if r_file:
                r_file.write("}\n")
                r_file.close()


class sdist(_sdist):

    def run(self):
        self.filelist = FileList()
        self.get_file_list()
        make_resource_module(self.filelist.files)

        r = super().run()

        assert len(self.archive_files) == 1
        print("filtering files and recompressing with 4K dictionary")
        filter_tar(self.archive_files[0])
        outbuf.seek(0)
        gzip_4k(outbuf, self.archive_files[0])

        return r


# For testing only
if __name__ == "__main__":
    filter_tar(sys.argv[1])
    outbuf.seek(0)
    gzip_4k(outbuf, sys.argv[1])
