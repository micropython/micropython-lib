from utime import *
from micropython import const

_TS_YEAR = const(0)
_TS_MON = const(1)
_TS_MDAY = const(2)
_TS_HOUR = const(3)
_TS_MIN = const(4)
_TS_SEC = const(5)
_TS_WDAY = const(6)
_TS_YDAY = const(7)
_TS_ISDST = const(8)

_WDAY = const(("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"))
_MDAY = const(
    (
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    )
)


def strftime(datefmt, ts):
    from io import StringIO

    fmtsp = False
    ftime = StringIO()
    for k in datefmt:
        if fmtsp:
            if k == "a":
                ftime.write(_WDAY[ts[_TS_WDAY]][0:3])
            elif k == "A":
                ftime.write(_WDAY[ts[_TS_WDAY]])
            elif k == "b":
                ftime.write(_MDAY[ts[_TS_MON] - 1][0:3])
            elif k == "B":
                ftime.write(_MDAY[ts[_TS_MON] - 1])
            elif k == "d":
                ftime.write("%02d" % ts[_TS_MDAY])
            elif k == "H":
                ftime.write("%02d" % ts[_TS_HOUR])
            elif k == "I":
                ftime.write("%02d" % (ts[_TS_HOUR] % 12))
            elif k == "j":
                ftime.write("%03d" % ts[_TS_YDAY])
            elif k == "m":
                ftime.write("%02d" % ts[_TS_MON])
            elif k == "M":
                ftime.write("%02d" % ts[_TS_MIN])
            elif k == "P":
                ftime.write("AM" if ts[_TS_HOUR] < 12 else "PM")
            elif k == "S":
                ftime.write("%02d" % ts[_TS_SEC])
            elif k == "w":
                ftime.write(str(ts[_TS_WDAY]))
            elif k == "y":
                ftime.write("%02d" % (ts[_TS_YEAR] % 100))
            elif k == "Y":
                ftime.write(str(ts[_TS_YEAR]))
            else:
                ftime.write(k)
            fmtsp = False
        elif k == "%":
            fmtsp = True
        else:
            ftime.write(k)
    val = ftime.getvalue()
    ftime.close()
    return val
