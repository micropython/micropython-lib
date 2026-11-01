# Regression test for the memory that PCRE2 allocates behind this module: the
# match data of every match, and every compiled pattern, have to be freed
# again.  Otherwise each call leaks a few kilobytes.
#
# The match data is freed by the call that created it.  A compiled pattern is
# freed by the garbage collector, through the weakref.finalize() that the
# pattern registers for itself, so a pattern that is no longer reachable does
# not have to be released by hand.
#
# The bounded cache that compile() keeps is covered as well: it must not grow
# past its limit, and the patterns that it drops have to be freed.

import gc
import re


def rss():
    # Resident set size in KiB, from the second field of /proc/self/statm.
    with open("/proc/self/statm") as f:
        return int(f.read().split()[1]) * 4096 // 1024


try:
    rss()
except OSError:
    # No /proc, so memory use cannot be measured here.
    print("SKIP")
    raise SystemExit


N = 4000
LIMIT = 256  # KiB


def check_no_leak(name, fn):
    # Run the calls once to let the MicroPython heap grow to its steady state,
    # so that only the memory allocated by PCRE2 is measured afterwards.
    for _ in range(N):
        fn()
    gc.collect()
    before = rss()
    for _ in range(N):
        fn()
    gc.collect()
    growth = rss() - before
    assert growth < LIMIT, "%s leaks %d KiB per %d calls (%d bytes per call)" % (
        name,
        growth,
        N,
        growth * 1024 // N,
    )


text = "He was carefully disguised but captured quickly by police."
p = re.compile("a(b)c")

# Matching with a compiled pattern.
check_no_leak("Pattern.search() with a match", lambda: p.search("xxabcxx"))
check_no_leak("Pattern.search() without a match", lambda: p.search("xxxxxxx"))
check_no_leak("Pattern.match()", lambda: p.match("abcxx"))
check_no_leak("Pattern.sub()", lambda: p.sub("z", "xxabcxx"))
check_no_leak("Pattern.split()", lambda: p.split("xxabcxx"))
check_no_leak("Pattern.findall()", lambda: p.findall("xxabcxx abc"))

# The module level functions, which compile a pattern of their own.
check_no_leak("re.search()", lambda: re.search("a(b)c", "xxabcxx"))
check_no_leak("re.match()", lambda: re.match("a(b)c", "abcxx"))
check_no_leak("re.sub()", lambda: re.sub("a", "z", "caaab"))
check_no_leak("re.split()", lambda: re.split(r"\W+", "Words, words, words."))
check_no_leak("re.findall()", lambda: re.findall(r"(\w+)ly", text))


# A pattern with several groups needs a larger match data block.
def many_groups():
    r = re.compile(r"(\w+)(\s+)(\w+)(\s+)(\w+)")
    assert r.search("one two three").groups() == ("one", " ", "two", " ", "three")


check_no_leak("pattern with several groups", many_groups)


# The path that does not produce a usable pattern must not leak either.
def failed_compile():
    try:
        re.compile("(")
    except AssertionError:
        pass


check_no_leak("re.compile() of a bad pattern", failed_compile)


# compile() returns the cached pattern, the way CPython does, so compiling the
# same pattern again does not allocate.
assert re.compile("a(b)c") is re.compile("a(b)c")
check_no_leak("re.compile() with the same pattern", lambda: re.compile("a(b)c"))


# The cache has to stay bounded, and a pattern that it drops has to be freed by
# the garbage collector.
counter = [0]


def distinct_patterns():
    counter[0] += 1
    re.search("a%dc" % counter[0], "xxabcxx")


# Push far more distinct patterns through the cache than it can hold: it has
# to stop growing.
for _ in range(re._MAXCACHE * 4):
    distinct_patterns()
assert len(re._cache) <= re._MAXCACHE, len(re._cache)

check_no_leak("re.search() with distinct patterns", distinct_patterns)
assert len(re._cache) <= re._MAXCACHE, len(re._cache)



def compile_distinct():
    counter[0] += 1
    re.compile("b%dc" % counter[0])


check_no_leak("re.compile() with distinct patterns", compile_distinct)
assert len(re._cache) <= re._MAXCACHE, len(re._cache)


# A replacement callback runs while sub() is still using its own pattern, and
# may push further patterns through the cache.  The reference that sub() holds
# has to keep that pattern alive across the callback.
def reentrant_repl(m):
    counter[0] += 1
    re.search("z%dz" % counter[0], "nothing here")
    return "z"


check_no_leak("re.sub() with a reentrant callback", lambda: re.sub("a", reentrant_repl, "caaab"))
assert len(re._cache) <= re._MAXCACHE, len(re._cache)
