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


class PCREMatch:

    def __init__(self, s, num_matches, offsets):
        self.s = s
        self.num = num_matches
        self.offsets = offsets

    def group(self, n):
        return self.s[self.offsets[n*2]:self.offsets[n*2+1]]


class PCREPattern:

    def __init__(self, compiled_ptn):
        self.obj = compiled_ptn

    def search(self, s):
        ov = array.array('i', [0, 0, 0] * 2)
        num = pcre_exec(self.obj, None, s, len(s), 0, 0, ov, len(ov))
        if num == -1:
            # No match
            return None
        return PCREMatch(s, num, ov)


def compile(pattern, flags=0):
    errptr = bytes(4)
    erroffset = bytes(4)
    regex = pcre_compile(pattern, flags, errptr, erroffset, None)
    assert regex
    return PCREPattern(regex)


def search(pattern, string, flags=0):
    r = compile(pattern, flags)
    return r.search(string)
