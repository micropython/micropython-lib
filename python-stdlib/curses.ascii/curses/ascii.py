"""Constants and membership tests for ASCII characters"""

NUL = 0x00  # ^@
SOH = 0x01  # ^A
STX = 0x02  # ^B
ETX = 0x03  # ^C
EOT = 0x04  # ^D
ENQ = 0x05  # ^E
ACK = 0x06  # ^F
BEL = 0x07  # ^G
BS = 0x08  # ^H
TAB = 0x09  # ^I
HT = 0x09  # ^I
LF = 0x0A  # ^J
NL = 0x0A  # ^J
VT = 0x0B  # ^K
FF = 0x0C  # ^L
CR = 0x0D  # ^M
SO = 0x0E  # ^N
SI = 0x0F  # ^O
DLE = 0x10  # ^P
DC1 = 0x11  # ^Q
DC2 = 0x12  # ^R
DC3 = 0x13  # ^S
DC4 = 0x14  # ^T
NAK = 0x15  # ^U
SYN = 0x16  # ^V
ETB = 0x17  # ^W
CAN = 0x18  # ^X
EM = 0x19  # ^Y
SUB = 0x1A  # ^Z
ESC = 0x1B  # ^[
FS = 0x1C  # ^\
GS = 0x1D  # ^]
RS = 0x1E  # ^^
US = 0x1F  # ^_
SP = 0x20  # space
DEL = 0x7F  # delete

controlnames = [
    "NUL",
    "SOH",
    "STX",
    "ETX",
    "EOT",
    "ENQ",
    "ACK",
    "BEL",
    "BS",
    "HT",
    "LF",
    "VT",
    "FF",
    "CR",
    "SO",
    "SI",
    "DLE",
    "DC1",
    "DC2",
    "DC3",
    "DC4",
    "NAK",
    "SYN",
    "ETB",
    "CAN",
    "EM",
    "SUB",
    "ESC",
    "FS",
    "GS",
    "RS",
    "US",
    "SP",
]


def _ctoi(c):
    return ord(c) if type(c) is str else c


def isalnum(c):
    return isalpha(c) or isdigit(c)


def isalpha(c):
    return isupper(c) or islower(c)


def isascii(c):
    return _ctoi(c) <= 127  # ?


def isblank(c):
    ch = _ctoi(c)
    return ch == 9 or ch == 32


def iscntrl(c):
    ch = _ctoi(c)
    return ch <= 31 or ch == 127


def isdigit(c):
    ch = _ctoi(c)
    return ch >= 48 and ch <= 57


def isgraph(c):
    ch = _ctoi(c)
    return ch >= 33 and ch <= 126


def islower(c):
    ch = _ctoi(c)
    return ch >= 97 and ch <= 122


def isprint(c):
    ch = _ctoi(c)
    return ch >= 32 and ch <= 126


def ispunct(c):
    ch = _ctoi(c)
    return (
        (ch >= 33 and ch <= 47)
        or (ch >= 58 and ch <= 64)
        or (ch >= 91 and ch <= 96)
        or (ch >= 123 and ch <= 126)
    )


def isspace(c):
    ch = _ctoi(c)
    return isblank(c) or (ch >= 10 and ch <= 13)


def isupper(c):
    ch = _ctoi(c)
    return ch >= 65 and ch <= 90


def isxdigit(c):
    ch = _ctoi(c)
    return isdigit(c) or (ch >= 65 and ch <= 70) or (ch >= 97 and ch <= 102)


def isctrl(c):
    return _ctoi(c) < 32


def ismeta(c):
    return _ctoi(c) > 127


def ascii(c):
    ch = _ctoi(c) & 0x7F
    return chr(ch) if type(c) is str else ch


def ctrl(c):
    ch = _ctoi(c) & 0x1F
    return chr(ch) if type(c) is str else ch


def alt(c):
    ch = _ctoi(c) | 0x80
    return chr(ch) if type(c) is str else ch


def unctrl(c):
    bits = _ctoi(c)
    if bits == 0x7F:
        rep = "^?"
    elif isprint(bits & 0x7F):
        rep = chr(bits & 0x7F)
    else:
        rep = "^" + chr(((bits & 0x7F) | 0x20) + 0x20)
    return "!" + rep if bits & 0x80 else rep
