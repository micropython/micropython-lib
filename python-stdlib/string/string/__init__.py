# Some strings for ctype-style character classification
whitespace = " \t\n\r\v\f"
ascii_lowercase = "abcdefghijklmnopqrstuvwxyz"
ascii_uppercase = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
ascii_letters = ascii_lowercase + ascii_uppercase
digits = "0123456789"
hexdigits = digits + "abcdef" + "ABCDEF"
octdigits = "01234567"
punctuation = """!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~"""
printable = digits + ascii_letters + punctuation + whitespace

__all__ = [
    "whitespace",
    "ascii_lowercase",
    "ascii_uppercase",
    "ascii_letters",
    "digits",
    "hexdigits",
    "octdigits",
    "punctuation",
    "printable",
    "translate",
]


def translate(s, map):
    import io

    sb = io.StringIO()
    for c in s:
        v = ord(c)
        if v in map:
            v = map[v]
            if isinstance(v, int):
                sb.write(chr(v))
            elif v is not None:
                sb.write(v)
        else:
            sb.write(c)
    return sb.getvalue()

try:
    from . import templatelib as _templatelib
except ImportError:
    pass
else:
    templatelib = _templatelib
    __all__.append("templatelib")
