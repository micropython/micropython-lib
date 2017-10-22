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
    exec("v=" + s, d)
    return d["v"]
