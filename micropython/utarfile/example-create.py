import sys
import utarfile

tarfile = sys.argv[1]
if not tarfile.endswith(".tar"):
    raise ValueError("Filename %s does not end with .tar" % tarfile)

t = utarfile.TarFile(sys.argv[1], "w")
for filename in sys.argv[2:]:
    t.add(filename)
t.close()
