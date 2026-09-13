import sys
import ffilib
import array
import uctypes

pcre2 = ffilib.open("libpcre2-8")

#       pcre2_code *pcre2_compile(PCRE2_SPTR pattern, PCRE2_SIZE length,
#           uint32_t options, int *errorcode, PCRE2_SIZE *erroroffset,
#           pcre2_compile_context *ccontext);
pcre2_compile = pcre2.func("p", "pcre2_compile_8", "siippp")

#       int pcre2_match(const pcre2_code *code, PCRE2_SPTR subject,
#           PCRE2_SIZE length, PCRE2_SIZE startoffset, uint32_t options,
#           pcre2_match_data *match_data, pcre2_match_context *mcontext);
pcre2_match = pcre2.func("i", "pcre2_match_8", "Psiiipp")

#       int pcre2_pattern_info(const pcre2_code *code, uint32_t what,
#           void *where);
pcre2_pattern_info = pcre2.func("i", "pcre2_pattern_info_8", "Pip")

#       PCRE2_SIZE *pcre2_get_ovector_pointer(pcre2_match_data *match_data);
pcre2_get_ovector_pointer = pcre2.func("p", "pcre2_get_ovector_pointer_8", "p")

#       void pcre2_code_free(pcre2_code *code);
pcre2_code_free = pcre2.func("v", "pcre2_code_free_8", "p")

#       void pcre2_match_data_free(pcre2_match_data *match_data);
pcre2_match_data_free = pcre2.func("v", "pcre2_match_data_free_8", "p")

#       pcre2_match_data *pcre2_match_data_create_from_pattern(const pcre2_code *code,
#           pcre2_general_context *gcontext);
pcre2_match_data_create_from_pattern = pcre2.func(
    "p", "pcre2_match_data_create_from_pattern_8", "Pp"
)

# PCRE2_SIZE that is of type size_t.
# Use ULONG as type to support both 32bit and 64bit.
PCRE2_SIZE_SIZE = uctypes.sizeof({"field": 0 | uctypes.ULONG})
PCRE2_SIZE_TYPE = "L"

# Real value in pcre2.h is 0xFFFFFFFF for 32bit and
# 0x0xFFFFFFFFFFFFFFFF for 64bit that is equivalent
# to -1
PCRE2_ZERO_TERMINATED = -1

# PCRE2_UNSET is used for offsets of groups that didn't participate in a match
# It's SIZE_MAX: 0xFFFFFFFF for 32bit, 0xFFFFFFFFFFFFFFFF for 64bit
PCRE2_UNSET = (1 << (PCRE2_SIZE_SIZE * 8)) - 1


IGNORECASE = I = 0x8
MULTILINE = M = 0x400
DOTALL = S = 0x20
VERBOSE = X = 0x80
PCRE2_ANCHORED = 0x80000000

# TODO. Note that Python3 has unicode by default
ASCII = A = 0
UNICODE = U = 0

PCRE2_INFO_CAPTURECOUNT = 0x4


class PCREMatch:
    def __init__(self, s, num_matches, offsets):
        self.s = s
        self.num = num_matches
        self.offsets = offsets

    def group(self, *n):
        if not n:
            return self.s[self.offsets[0] : self.offsets[1]]
        if len(n) == 1:
            return None if self.offsets[n[0] * 2] == PCRE2_UNSET else self.s[self.offsets[n[0] * 2] : self.offsets[n[0] * 2 + 1]]
        return tuple(None if self.offsets[i * 2] == PCRE2_UNSET else self.s[self.offsets[i * 2] : self.offsets[i * 2 + 1]] for i in n)

    def groups(self, default=None):
        return tuple(default if self.offsets[(i + 1) * 2] == PCRE2_UNSET else self.group(i + 1) for i in range(self.num - 1))

    def start(self, n=0):
        return self.offsets[n * 2]

    def end(self, n=0):
        return self.offsets[n * 2 + 1]

    def span(self, n=0):
        return self.offsets[n * 2], self.offsets[n * 2 + 1]


class PCREPattern:
    def __init__(self, compiled_ptn):
        self.obj = compiled_ptn
        self.key = None  # set while this pattern is held by the cache

    def _free(self):
        # MicroPython does not run __del__ on instances of Python classes, so
        # the compiled pattern cannot be released by the garbage collector and
        # has to be freed explicitly.
        if self.obj is not None:
            if self.key is not None:
                # Drop the pattern from the cache first, so that nothing hands
                # out a pointer that is about to become invalid.
                del _cache[self.key]
                self.key = None
            pcre2_code_free(self.obj)
            self.obj = None

    def search(self, s, pos=0, endpos=-1, _flags=0):
        assert endpos == -1, "pos: %d, endpos: %d" % (pos, endpos)
        buf = array.array("i", [0])
        pcre2_pattern_info(self.obj, PCRE2_INFO_CAPTURECOUNT, buf)
        cap_count = buf[0]
        match_data = pcre2_match_data_create_from_pattern(self.obj, None)
        try:
            num = pcre2_match(self.obj, s, len(s), pos, _flags, match_data, None)
            if num == -1:
                # No match
                return None
            ov_ptr = pcre2_get_ovector_pointer(match_data)
            # pcre2_get_ovector_pointer return PCRE2_SIZE.  The offsets are
            # copied out here, because the match data is freed below.
            ov_buf = uctypes.bytearray_at(ov_ptr, PCRE2_SIZE_SIZE * (cap_count + 1) * 2)
            ov = array.array(PCRE2_SIZE_TYPE, ov_buf)
        finally:
            pcre2_match_data_free(match_data)
        # We don't care how many matching subexpressions we got, we
        # care only about total # of capturing ones (including empty)
        return PCREMatch(s, cap_count + 1, ov)

    def match(self, s, pos=0, endpos=-1):
        return self.search(s, pos, endpos, PCRE2_ANCHORED)

    def sub(self, repl, s, count=0):
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
            if count != 0:
                count -= 1
                if count == 0:
                    return res + s
        return res

    def split(self, s, maxsplit=0):
        res = []
        while True:
            m = self.search(s)
            g = None
            if m:
                g = m.group(0)
            if not m or not g:
                res.append(s)
                return res
            beg, end = m.span(0)
            res.append(s[:beg])
            if m.num > 1:
                res.extend(m.groups())
            s = s[end:]
            if maxsplit > 0:
                maxsplit -= 1
                if maxsplit == 0:
                    res.append(s)
                    return res

    def findall(self, s):
        res = []
        start = 0
        while True:
            m = self.search(s, start)
            if not m:
                return res
            if m.num == 1:
                res.append(m.group(0))
            elif m.num == 2:
                res.append(m.group(1))
            else:
                res.append(m.groups())
            beg, end = m.span(0)
            start = end


def _compile(pattern, flags):
    # These are output arguments and must be of the size that pcre2_compile()
    # writes: int for the error code, PCRE2_SIZE for the offset.
    errcode = bytes(4)
    erroffset = bytes(PCRE2_SIZE_SIZE)
    regex = pcre2_compile(pattern, PCRE2_ZERO_TERMINATED, flags, errcode, erroffset, None)
    assert regex, "compile error %d at %d" % (
        int.from_bytes(errcode, sys.byteorder),
        int.from_bytes(erroffset, sys.byteorder),
    )
    return PCREPattern(regex)


# Compiled patterns are cached, the way CPython does it, so that using the same
# pattern again does not compile it a second time.  compile() returns the
# cached pattern, so re.compile(p) is re.compile(p), as in CPython.
#
# The cache owns the patterns it holds and never evicts them.  A pattern that
# is still being used, either by the caller or by a call further up the stack,
# must not be freed underneath it; a replacement callback passed to sub() can
# otherwise trigger exactly that.  The cache is bounded instead: once it is
# full, further patterns are compiled and, where this module owns them, freed
# again after use.
_MAXCACHE = 32
_cache = {}


def _cached(pattern, flags):
    # Return the compiled pattern, and whether the caller has to free it.
    key = (pattern, flags)
    r = _cache.get(key)
    if r is not None:
        return r, False
    r = _compile(pattern, flags)
    if len(_cache) < _MAXCACHE:
        _cache[key] = r
        r.key = key
        return r, False
    return r, True


def compile(pattern, flags=0):
    # The pattern belongs to the caller, so it is never freed here.
    return _cached(pattern, flags)[0]


def search(pattern, string, flags=0):
    r, owned = _cached(pattern, flags)
    try:
        return r.search(string)
    finally:
        if owned:
            r._free()


def match(pattern, string, flags=0):
    r, owned = _cached(pattern, flags | PCRE2_ANCHORED)
    try:
        return r.search(string)
    finally:
        if owned:
            r._free()


def sub(pattern, repl, s, count=0, flags=0):
    r, owned = _cached(pattern, flags)
    try:
        return r.sub(repl, s, count)
    finally:
        if owned:
            r._free()


def split(pattern, s, maxsplit=0, flags=0):
    r, owned = _cached(pattern, flags)
    try:
        return r.split(s, maxsplit)
    finally:
        if owned:
            r._free()


def findall(pattern, s, flags=0):
    r, owned = _cached(pattern, flags)
    try:
        return r.findall(s)
    finally:
        if owned:
            r._free()


def escape(s):
    res = ""
    for c in s:
        if "0" <= c <= "9" or "A" <= c <= "Z" or "a" <= c <= "z" or c == "_":
            res += c
        else:
            res += "\\" + c
    return res
