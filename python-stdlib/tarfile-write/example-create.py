""" tar create writes a new tar file containing the specified files."""
import sys
import tarfile

if len(sys.argv) < 2:
    raise ValueError("Usage: %s outputfile.tar inputfile1 ..." % sys.argv[0])

tarfile = sys.argv[1]
if not tarfile.endswith(".tar"):
    raise ValueError("Filename %s does not end with .tar" % tarfile)

with tarfile.TarFile(sys.argv[1], "w") as t:
    for filename in sys.argv[2:]:
        t.add(filename)
