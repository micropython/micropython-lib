import os


sep = "/"


def normcase(s):
    return s


def normpath(s):
    return s


def abspath(s):
    if s[0] != sep:
        return os.getcwd() + sep + s
    return s


def join(*args):
    # TODO: this is non-compliant
    if type(args[0]) is bytes:
        return bytes(sep).join(args)
    else:
        return sep.join(args)


def split(path):
    if path == "":
        return ("", "")
    r = path.rsplit(sep, 1)
    if len(r) == 1:
        return ("", path)
    head = r[0]  # .rstrip("/")
    if not head:
        head = sep
    return (head, r[1])


def dirname(path):
    return split(path)[0]


def basename(path):
    return split(path)[1]


def exists(path):
    try:
        os.stat(path)
        return True
    except OSError:
        return False


# TODO
lexists = exists


def isdir(path):
    try:
        mode = os.stat(path)[0]
        return mode & 0o040000
    except OSError:
        return False


def isfile(path):
    try:
        return bool(os.stat(path)[0] & 0x8000)
    except OSError:
        return False


def expanduser(s):
    if s == "~" or s.startswith("~" + sep):
        h = os.getenv("HOME")
        return h + s[1:]
    if s[0] == "~":
        # Sorry folks, follow conventions
        return "/home/" + s[1:]
    return s
