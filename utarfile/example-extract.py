import sys
import os
import shutil
import utarfile

t = utarfile.TarFile(sys.argv[1])
for i in t:
    print(i)
    if i.type == utarfile.DIRTYPE:
        os.makedirs(i.name)
    else:
        f1 = t.extractfile(i)
        f2 = open(i.name, "wb")
        shutil.copyfileobj(f1, f2)
        f2.close()
        
