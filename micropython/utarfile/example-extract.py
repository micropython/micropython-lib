import sys
import os
import utarfile

if len(sys.argv) < 2:
    raise ValueError("Usage: %s inputfile.tar" % sys.argv[0])

t = utarfile.TarFile(sys.argv[1])
for i in t:
    print(i.name)
    if i.type == utarfile.DIRTYPE:
        os.mkdir(i.name)
    else:
        f = t.extractfile(i)
        with open(i.name, "wb") as of:
            of.write(f.read())
