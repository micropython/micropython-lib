HIGHEST_PROTOCOL = 0

def dump(obj, f, proto=0):
    f.write(repr(obj))

def dumps(obj, proto=0):
    return repr(obj)

def load(f):
    s = f.read()
    return loads(s)

def loads(s):
    d = {}
    if "(" in s:
        qualname = s.split("(", 1)[0]
        if "." in qualname:
            pkg = qualname.rsplit(".", 1)[0]
            mod = __import__(pkg)
            d[pkg] = mod
    exec("v=" + s, d)
    return d["v"]
