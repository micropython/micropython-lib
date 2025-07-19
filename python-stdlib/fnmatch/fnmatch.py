"""Filename matching with shell patterns.

fnmatch(FILENAME, PATTERN) matches according to the local convention.
fnmatchcase(FILENAME, PATTERN) always takes case in account.

The functions operate by translating the pattern into a regular
expression.  They cache the compiled regular expressions for speed.

The function translate(PATTERN) returns a regular expression
corresponding to PATTERN.  (It does not compile it.)
"""
import re

try:
    from os.path import normcase
except ImportError:

    def normcase(s):
        """
        From os.path.normcase
        Normalize the case of a pathname. On Windows, convert all characters
        in the pathname to lowercase, and also convert forward slashes to
        backward slashes. On other operating systems, return the path unchanged.
        """
        return s


__all__ = ["filter", "fnmatch", "fnmatchcase", "translate"]


def fnmatch(name, pat):
    """Test whether FILENAME matches PATTERN.

    Patterns are Unix shell style:

    *       matches everything
    ?       matches any single character
    [seq]   matches any character in seq
    [!seq]  matches any char not in seq

    An initial period in FILENAME is not special.
    Both FILENAME and PATTERN are first case-normalized
    if the operating system requires it.
    If you don't want this, use fnmatchcase(FILENAME, PATTERN).
    """
    name = normcase(name)
    pat = normcase(pat)
    return fnmatchcase(name, pat)


# @functools.lru_cache(maxsize=256, typed=True)
def _compile_pattern(pat):
    if isinstance(pat, bytes):
        pat_str = str(pat, "ISO-8859-1")
        res_str = translate(pat_str)
        res = bytes(res_str, "ISO-8859-1")
    else:
        res = translate(pat)

    try:
        ptn = re.compile(res)
    except ValueError:
        # re1.5 doesn't support all regex features
        if res.startswith("(?ms)"):
            res = res[5:]
        if res.endswith("\\Z"):
            res = res[:-2] + "$"
        ptn = re.compile(res)

    return ptn.match


def filter(names, pat):
    """Return the subset of the list NAMES that match PAT."""
    result = []
    pat = normcase(pat)
    match = _compile_pattern(pat)
    for name in names:
        if match(normcase(name)):
            result.append(name)
    return result


def fnmatchcase(name, pat):
    """Test whether FILENAME matches PATTERN, including case.

    This is a version of fnmatch() which doesn't case-normalize
    its arguments.
    """
    match = _compile_pattern(pat)
    return match(name) is not None


def translate(pat):
    """Translate a shell PATTERN to a regular expression.

    There is no way to quote meta-characters.
    """

    i, n = 0, len(pat)
    res = ""
    while i < n:
        c = pat[i]
        i = i + 1
        if c == "*":
            res = res + ".*"
        elif c == "?":
            res = res + "."
        elif c == "[":
            j = i
            if j < n and pat[j] == "!":
                j = j + 1
            if j < n and pat[j] == "]":
                j = j + 1
            while j < n and pat[j] != "]":
                j = j + 1
            if j >= n:
                res = res + "\\["
            else:
                stuff = pat[i:j].replace("\\", "\\\\")
                i = j + 1
                if stuff[0] == "!":
                    stuff = "^" + stuff[1:]
                elif stuff[0] == "^":
                    stuff = "\\" + stuff
                res = "%s[%s]" % (res, stuff)
        else:
            try:
                res = res + re.escape(c)
            except AttributeError:
                # Using ure rather than re-pcre
                res = res + re_escape(c)
    # Original patterns is undefined, see http://bugs.python.org/issue21464
    return "(?ms)" + res + "\Z"


def re_escape(pattern):
    # Replacement minimal re.escape for ure compatibility
    return re.sub(r"([\^\$\.\|\?\*\+\(\)\[\\])", r"\\\1", pattern)
