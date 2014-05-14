import os


def normcase(s):
    return s

def normpath(s):
    return s

def join(*args):
    # TODO: this is non-compliant
    return "/".join(args)

def split(path):
    if path == "":
        return ("", "")
    r = path.rsplit("/", 1)
    if len(r) == 1:
        return ("", path)
    head = r[0] #.rstrip("/")
    if not head:
        head = "/"
    return (head, r[1])

def exists(path):
    return os.access(path, os.F_OK)
