from utime import *
import ffi
import _libc
import array

libc = _libc.get()

# struct tm *gmtime(const time_t *timep);
# struct tm *localtime(const time_t *timep);
# size_t strftime(char *s, size_t max, const char *format,
#                       const struct tm *tm);
gmtime_ = libc.func("P", "gmtime", "P")
localtime_ = libc.func("P", "localtime", "P")
strftime_ = libc.func("i", "strftime", "sisP")


def strftime(format, t=None):
    if t is None:
        t = time()

    t = int(t)
    a = array.array('i', [t])
    tm_p = localtime_(a)
    buf = bytearray(32)
    l = strftime_(buf, 32, format, tm_p)
    return str(buf[:l], "utf-8")
