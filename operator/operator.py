def attrgetter(attr):
    assert "." not in attr
    def _attrgetter(obj):
        return getattr(obj, attr)
    return _attrgetter


def lt(a, b):
    return a < b

def le(a, b):
    return a <= b

def gt(a, b):
    return a > b

def ge(a, b):
    return a >= b

def eq(a, b):
    return a == b

def ne(a, b):
    return a != b

def add(a, b):
    return a + b

def and_(a, b):
    return a & b

def floordiv(a, b):
    return a // b

def inv(a):
    return ~a

invert = inv

def mod(a, b):
    return a % b

def mul(a, b):
    return a * b

def neg(a):
    return 0 - a

def or_(a, b):
    return a | b

def pow(a, b):
    return a ** b

def sub(a, b):
    return a - b

def truediv(a, b):
    return a / b

def xor(a, b):
    return a ^ b

def floordiv(a, b):
    return a // b
