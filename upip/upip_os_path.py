import upip_os


def normcase(s):
    return s

def normpath(s):
    return s

def abspath(s):
    return upip_os.getcwd() + "/" + s

def join(*args):
    # TODO: this is non-compliant
    if type(args[0]) is bytes:
        return b"/".join(args)
    else:
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

def dirname(path):
    return split(path)[0]

def basename(path):
    return split(path)[1]

def exists(path):
    return upip_os.access(path, os.F_OK)

# TODO
lexists = exists

def isdir(path):
    import upip_stat
    try:
        mode = upip_os.stat(path)[0]
        return upip_stat.S_ISDIR(mode)
    except OSError:
        return False


def expanduser(s):
    if s == "~" or s.startswith("~/"):
        h = upip_os.getenv("HOME")
        return h + s[1:]
    if s[0] == "~":
        # Sorry folks, follow conventions
        return "/home/" + s[1:]
    return s
