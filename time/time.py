from utime import *
import ustruct
import uctypes
import ffi
import ffilib
import array

libc = ffilib.libc()

# struct tm *gmtime(const time_t *timep);
# struct tm *localtime(const time_t *timep);
# size_t strftime(char *s, size_t max, const char *format,
#                       const struct tm *tm);
gmtime_ = libc.func("P", "gmtime", "P")
localtime_ = libc.func("P", "localtime", "P")
strftime_ = libc.func("i", "strftime", "sisP")
mktime_ = libc.func("i", "mktime", "P")


def _tuple_to_c_tm(t):
    return ustruct.pack("@iiiiiiiii", t[5], t[4], t[3], t[2], t[1] - 1, t[0] - 1900, (t[6] + 1) % 7, t[7] - 1, t[8])


def _c_tm_to_tuple(tm):
    t = ustruct.unpack("@iiiiiiiii", tm)
    return tuple([t[5] + 1900, t[4] + 1, t[3], t[2], t[1], t[0], (t[6] - 1) % 7, t[7] + 1, t[8]])


def strftime(format, t=None):
    if (t is None):
        t = localtime() 

    buf = bytearray(32)
    l = strftime_(buf, 32, format, _tuple_to_c_tm(t))
    return str(buf[:l], "utf-8")



def localtime(t=None):
    if t is None:
        t = time()

    t = int(t)
    a = ustruct.pack('i', t)
    tm_p = localtime_(a)
    return _c_tm_to_tuple(uctypes.bytearray_at(tm_p, 36))


def gmtime(t=None):
    if t is None:
        t = time()

    t = int(t)
    a = ustruct.pack('i', t)
    tm_p = gmtime_(a)
    return _c_tm_to_tuple(uctypes.bytearray_at(tm_p, 36))


def mktime(tt):
    return mktime_(_tuple_to_c_tm(tt))


def perf_counter():
    return time()

def process_time():
    return clock()
