# Reimplement, because CPython3.3 impl is rather bloated
import os


def rmtree(top):
    for path, dirs, files in os.walk(top, False):
        for f in files:
            os.unlink(path + "/" + f)
        os.rmdir(path)
