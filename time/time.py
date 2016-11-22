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

class struct_time:
    def __init__(self, tm_year, tm_mon, tm_mday, tm_hour, tm_min, tm_sec, tm_wday, tm_yday, tm_isdst, tm_gmtoff=0, tm_zone='UTC'):
        self.tm_year = tm_year
        self.tm_mon = tm_mon
        self.tm_mday = tm_mday
        self.tm_hour = tm_hour
        self.tm_min = tm_min
        self.tm_sec = tm_sec
        self.tm_wday = tm_wday
        self.tm_yday = tm_yday
        self.tm_isdst = tm_isdst
        self.tm_gmtoff = tm_gmtoff
        self.tm_zone = tm_zone

    def __iter__(self):
        for i in [
            self.tm_year, self.tm_mon, self.tm_mday, self.tm_hour, self.tm_min,
            self.tm_sec, self.tm_wday, self.tm_yday, self.tm_isdst
        ]:
            yield i

    def __repr__(self):
        return "time.struct_time(tm_year=%d, tm_mon=%d, tm_mday=%d, tm_hour=%d, tm_min=%d, tm_sec=%d, tm_wday=%d, tm_yday=%d, tm_isdst=%d)" % (
            self.tm_year, self.tm_mon, self.tm_mday, self.tm_hour,
            self.tm_min, self.tm_sec, self.tm_wday, self.tm_yday, self.tm_isdst
        )


def _struct_time_to_c_tm(st):
    t = tuple(st)
    return ustruct.pack("@iiiiiiiiilP", t[5], t[4], t[3], t[2], t[1] - 1, t[0] - 1900, (t[6] + 1) % 7, t[7] - 1, t[8], st.tm_gmtoff, 0)


def _c_tm_to_struct_time(tm):
    t = ustruct.unpack("@iiiiiiiiiilP", tm)
    buf = bytearray(32)
    l = strftime_(buf, 32, "%Z", tm)
    tm_zone = str(buf[:l], "utf-8")
    return struct_time(tm_year=t[5] + 1900, tm_mon=t[4] + 1, tm_mday=t[3], tm_hour=t[2], tm_min=t[1], tm_sec=t[0], tm_wday=(t[6] - 1) % 7, tm_yday=t[7] + 1, tm_isdst=t[8], tm_gmtoff=t[9], tm_zone=tm_zone)


def strftime(format, t=None):
    if t is None:
        t = time()

    t = int(t)
    a = array.array('i', [t])
    tm_p = localtime_(a)
    buf = bytearray(32)
    l = strftime_(buf, 32, format, tm_p)
    return str(buf[:l], "utf-8")


def localtime(t=None):
    if t is None:
        t = time()

    t = int(t)
    a = ustruct.pack('i', t)
    tm_p = localtime_(a)
    return _c_tm_to_struct_time(uctypes.bytearray_at(tm_p, 52))


def gmtime(t=None):
    if t is None:
        t = time()

    t = int(t)
    a = ustruct.pack('i', t)
    tm_p = gmtime_(a)
    return _c_tm_to_struct_time(uctypes.bytearray_at(tm_p, 52))


def mktime(tt):
    return mktime_(_struct_time_to_c_tm(tt))


def perf_counter():
    return time()

def process_time():
    return clock()
