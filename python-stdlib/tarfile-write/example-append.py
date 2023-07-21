""" tar append writes additional files to the end of an existing tar file."""
import os
import sys
import tarfile

if len(sys.argv) < 2:
    raise ValueError("Usage: %s appendfile.tar newinputfile1 ..." % sys.argv[0])

tarfile = sys.argv[1]
if not tarfile.endswith(".tar"):
    raise ValueError("Filename %s does not end with .tar" % tarfile)

with tarfile.TarFile(sys.argv[1], "a") as t:
    for filename in sys.argv[2:]:
        t.add(filename)
