import sys
import os
import tarfile

if len(sys.argv) < 2:
    raise ValueError("Usage: %s inputfile.tar" % sys.argv[0])

t = tarfile.TarFile(sys.argv[1])
for i in t:
    print(i.name)
    if i.type == tarfile.DIRTYPE:
        os.mkdir(i.name)
    else:
        f = t.extractfile(i)
        with open(i.name, "wb") as of:
            of.write(f.read())
