def dump(obj, f):
    f.write(repr(obj))

def dumps(obj):
    return repr(obj)

def load(f):
    s = f.read()
    return loads(s)

def loads(s):
    d = {}
    exec("v=" + s, d)
    return d["v"]
