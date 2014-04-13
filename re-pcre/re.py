import ffi
import array


pcre = ffi.open("libpcre.so.3")

#       pcre *pcre_compile(const char *pattern, int options,
#            const char **errptr, int *erroffset,
#            const unsigned char *tableptr);
pcre_compile = pcre.func("p", "pcre_compile", "sipps")

#       int pcre_exec(const pcre *code, const pcre_extra *extra,
#            const char *subject, int length, int startoffset,
#            int options, int *ovector, int ovecsize);
pcre_exec = pcre.func("i", "pcre_exec", "ppsiiipi")

#       int pcre_fullinfo(const pcre *code, const pcre_extra *extra,
#            int what, void *where);
pcre_fullinfo = pcre.func("i", "pcre_fullinfo", "ppip")


IGNORECASE = I = 1
MULTILINE = M = 2
DOTALL = S = 4
VERBOSE = X = 8
PCRE_ANCHORED = 0x10

# TODO. Note that Python3 has unicode by default
ASCII = A = 0
UNICODE = U = 0

PCRE_INFO_CAPTURECOUNT = 2


class PCREMatch:

    def __init__(self, s, num_matches, offsets):
        self.s = s
        self.num = num_matches
        self.offsets = offsets

    def group(self, n):
        return self.s[self.offsets[n*2]:self.offsets[n*2+1]]

    def groups(self, default=None):
        assert default is None
        return tuple(self.group(i + 1) for i in range(self.num - 1))

    def start(self, n=0):
        return self.offsets[n*2]

    def end(self, n=0):
        return self.offsets[n*2+1]

    def span(self, n=0):
        return self.offsets[n*2], self.offsets[n*2+1]


class PCREPattern:

    def __init__(self, compiled_ptn):
        self.obj = compiled_ptn

    def search(self, s, pos=0, endpos=-1, _flags=0):
        assert endpos == -1, "pos: %d, endpos: %d" % (pos, endpos)
        buf = bytes(4)
        pcre_fullinfo(self.obj, None, PCRE_INFO_CAPTURECOUNT, buf)
        cap_count = int.from_bytes(buf)
        ov = array.array('i', [0, 0, 0] * (cap_count + 1))
        num = pcre_exec(self.obj, None, s, len(s), pos, _flags, ov, len(ov))
        if num == -1:
            # No match
            return None
        # We don't care how many matching subexpressions we got, we
        # care only about total # of capturing ones (including empty)
        return PCREMatch(s, cap_count + 1, ov)

    def match(self, s, pos=0, endpos=-1):
        return self.search(s, pos, endpos, PCRE_ANCHORED)

    def sub(self, repl, s):
        if not callable(repl):
            assert "\\" not in repl, "Backrefs not implemented"
        res = ""
        while s:
            m = self.search(s)
            if not m:
                return res + s
            beg, end = m.span()
            res += s[:beg]
            if callable(repl):
                res += repl(m)
            else:
                res += repl
            s = s[end:]


def compile(pattern, flags=0):
    errptr = bytes(4)
    erroffset = bytes(4)
    regex = pcre_compile(pattern, flags, errptr, erroffset, None)
    assert regex
    return PCREPattern(regex)


def search(pattern, string, flags=0):
    r = compile(pattern, flags)
    return r.search(string)


def match(pattern, string, flags=0):
    r = compile(pattern, flags | PCRE_ANCHORED)
    return r.search(string)


def sub(pattern, repl, s, count=0, flags=0):
    r = compile(pattern, flags)
    return r.sub(repl, s)
