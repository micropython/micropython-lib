# datetime.py

import time as _time

__version__ = "2.0.0"

_DBM = (0, 0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334)
_DIM = (0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
_TIME_SPEC = ("auto", "hours", "minutes", "seconds", "milliseconds", "microseconds")


def _is_leap(year):
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def _days_before_year(year):
    # year -> number of days before January 1st of year.
    y = year - 1
    return y * 365 + y // 4 - y // 100 + y // 400


def _days_in_month(year, month):
    # year, month -> number of days in that month in that year.
    if month == 2 and _is_leap(year):
        return 29
    return _DIM[month]


def _days_before_month(year, month):
    # year, month -> number of days in year preceding first day of month.
    return _DBM[month] + (month > 2 and _is_leap(year))


def _ymd2ord(year, month, day):
    # year, month, day -> ordinal, considering 01-Jan-0001 as day 1.
    return _days_before_year(year) + _days_before_month(year, month) + day


def _ord2ymd(n):
    # ordinal -> (year, month, day), considering 01-Jan-0001 as day 1.
    n -= 1
    n400, n = divmod(n, 146_097)
    year = n400 * 400 + 1
    n100, n = divmod(n, 36_524)
    n4, n = divmod(n, 1_461)
    n1, n = divmod(n, 365)
    year += n100 * 100 + n4 * 4 + n1
    if n1 == 4 or n100 == 4:
        return year - 1, 12, 31
    month = (n + 50) >> 5
    preceding = _days_before_month(year, month)
    if preceding > n:
        month -= 1
        preceding -= _days_in_month(year, month)
    n -= preceding
    return year, month, n + 1


MINYEAR = 1
MAXYEAR = 9_999


class timedelta:
    def __init__(
        self, days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=0
    ):
        s = (((weeks * 7 + days) * 24 + hours) * 60 + minutes) * 60 + seconds
        self._us = (s * 1000 + milliseconds) * 1000 + microseconds

    def __repr__(self):
        return "datetime.timedelta(microseconds={})".format(self._us)

    def total_seconds(self):
        return self._us / 1_000_000

    @property
    def days(self):
        return self._tuple(2)[0]

    @property
    def seconds(self):
        return self._tuple(3)[1]

    @property
    def microseconds(self):
        return self._tuple(3)[2]

    def __add__(self, other):
        if isinstance(other, datetime):
            return other.__add__(self)
        else:
            us = other._us
        return timedelta(0, 0, self._us + us)

    def __sub__(self, other):
        return timedelta(0, 0, self._us - other._us)

    def __neg__(self):
        return timedelta(0, 0, -self._us)

    def __pos__(self):
        return self

    def __abs__(self):
        return -self if self._us < 0 else self

    def __mul__(self, other):
        return timedelta(0, 0, round(other * self._us))

    __rmul__ = __mul__

    def __truediv__(self, other):
        if isinstance(other, timedelta):
            return self._us / other._us
        else:
            return timedelta(0, 0, round(self._us / other))

    def __floordiv__(self, other):
        if isinstance(other, timedelta):
            return self._us // other._us
        else:
            return timedelta(0, 0, int(self._us // other))

    def __mod__(self, other):
        return timedelta(0, 0, self._us % other._us)

    def __divmod__(self, other):
        q, r = divmod(self._us, other._us)
        return q, timedelta(0, 0, r)

    def __eq__(self, other):
        return self._us == other._us

    def __le__(self, other):
        return self._us <= other._us

    def __lt__(self, other):
        return self._us < other._us

    def __ge__(self, other):
        return self._us >= other._us

    def __gt__(self, other):
        return self._us > other._us

    def __bool__(self):
        return self._us != 0

    def __str__(self):
        return self._format(0x40)

    def __hash__(self):
        if not hasattr(self, "_hash"):
            self._hash = hash(self._us)
        return self._hash

    def isoformat(self):
        return self._format(0)

    def _format(self, spec=0):
        if self._us >= 0:
            td = self
            g = ""
        else:
            td = -self
            g = "-"
        d, h, m, s, us = td._tuple(5)
        ms, us = divmod(us, 1000)
        r = ""
        if spec & 0x40:
            spec &= ~0x40
            hr = str(h)
        else:
            hr = f"{h:02d}"
        if spec & 0x20:
            spec &= ~0x20
            spec |= 0x10
            r += "UTC"
        if spec & 0x10:
            spec &= ~0x10
            if not g:
                g = "+"
        if d:
            p = "s" if d > 1 else ""
            r += f"{g}{d} day{p}, "
            g = ""
        if spec == 0:
            spec = 5 if (ms or us) else 3
        if spec >= 1 or h:
            r += f"{g}{hr}"
            if spec >= 2 or m:
                r += f":{m:02d}"
                if spec >= 3 or s:
                    r += f":{s:02d}"
                    if spec >= 4 or ms:
                        r += f".{ms:03d}"
                        if spec >= 5 or us:
                            r += f"{us:03d}"
        return r

    def tuple(self):
        return self._tuple(5)

    def _tuple(self, n):
        d, us = divmod(self._us, 86_400_000_000)
        if n == 2:
            return d, us
        s, us = divmod(us, 1_000_000)
        if n == 3:
            return d, s, us
        h, s = divmod(s, 3600)
        m, s = divmod(s, 60)
        return d, h, m, s, us


timedelta.min = timedelta(days=-999_999_999)
timedelta.max = timedelta(days=999_999_999, hours=23, minutes=59, seconds=59, microseconds=999_999)
timedelta.resolution = timedelta(microseconds=1)


class tzinfo:
    # abstract class
    def tzname(self, dt):
        raise NotImplementedError

    def utcoffset(self, dt):
        raise NotImplementedError

    def dst(self, dt):
        raise NotImplementedError

    def fromutc(self, dt):
        if dt._time._tz is not self:
            raise ValueError

        # See original datetime.py for an explanation of this algorithm.
        dtoff = dt.utcoffset()
        dtdst = dt.dst()
        delta = dtoff - dtdst
        if delta:
            dt += delta
            dtdst = dt.dst()
        return dt + dtdst

    def isoformat(self, dt):
        return self.utcoffset(dt)._format(0x12)


class timezone(tzinfo):
    def __init__(self, offset, name=None):
        if not (abs(offset._us) < 86_400_000_000):
            raise ValueError
        self._offset = offset
        self._name = name

    def __repr__(self):
        return "datetime.timezone({}, {})".format(repr(self._offset), repr(self._name))

    def __eq__(self, other):
        if isinstance(other, timezone):
            return self._offset == other._offset
        return NotImplemented

    def __str__(self):
        return self.tzname(None)

    def __hash__(self):
        if not hasattr(self, "_hash"):
            self._hash = hash((self._offset, self._name))
        return self._hash

    def utcoffset(self, dt):
        return self._offset

    def dst(self, dt):
        return None

    def tzname(self, dt):
        if self._name:
            return self._name
        if dt:
            return self.isoformat(dt)
        return self._offset._format(0x22)

    def fromutc(self, dt):
        return dt + self._offset


timezone.utc = timezone(timedelta(0))


class time:
    def __init__(self, hour=0, minute=0, second=0, microsecond=0, tzinfo=None):
        if (
            0 <= hour < 24
            and 0 <= minute < 60
            and 0 <= second < 60
            and 0 <= microsecond < 1_000_000
        ) or (hour == 0 and minute == 0 and second == 0 and 0 < microsecond < 86_400_000_000):
            self._td = timedelta(0, second, microsecond, 0, minute, hour)
        else:
            raise ValueError
        self._tz = tzinfo

    @staticmethod
    def fromisoformat(s):
        hour = 0
        minute = 0
        sec = 0
        usec = 0
        tz_sign = ""
        tz_hour = 0
        tz_minute = 0
        tz_sec = 0
        tz_usec = 0
        l = len(s)
        i = 0
        if l < 2:
            raise ValueError
        i += 2
        hour = int(s[i - 2 : i])
        if l > i and s[i] == ":":
            i += 3
            if l - i < 0:
                raise ValueError
            minute = int(s[i - 2 : i])
            if l > i and s[i] == ":":
                i += 3
                if l - i < 0:
                    raise ValueError
                sec = int(s[i - 2 : i])
                if l > i and s[i] == ".":
                    i += 4
                    if l - i < 0:
                        raise ValueError
                    usec = 1000 * int(s[i - 3 : i])
                    if l > i and s[i] != "+":
                        i += 3
                        if l - i < 0:
                            raise ValueError
                        usec += int(s[i - 3 : i])
        if l > i:
            if s[i] not in "+-":
                raise ValueError
            tz_sign = s[i]
            i += 6
            if l - i < 0:
                raise ValueError
            tz_hour = int(s[i - 5 : i - 3])
            tz_minute = int(s[i - 2 : i])
            if l > i and s[i] == ":":
                i += 3
                if l - i < 0:
                    raise ValueError
                tz_sec = int(s[i - 2 : i])
                if l > i and s[i] == ".":
                    i += 7
                    if l - i < 0:
                        raise ValueError
                    tz_usec = int(s[i - 6 : i])
        if l != i:
            raise ValueError
        if tz_sign:
            td = timedelta(hours=tz_hour, minutes=tz_minute, seconds=tz_sec, microseconds=tz_usec)
            if tz_sign == "-":
                td = -td
            tz = timezone(td)
        else:
            tz = None
        return time(hour, minute, sec, usec, tz)

    @property
    def hour(self):
        return self.tuple()[0]

    @property
    def minute(self):
        return self.tuple()[1]

    @property
    def second(self):
        return self.tuple()[2]

    @property
    def microsecond(self):
        return self.tuple()[3]

    @property
    def tzinfo(self):
        return self._tz

    def replace(self, hour=None, minute=None, second=None, microsecond=None, tzinfo=True):
        h, m, s, us, tz = self.tuple()
        if hour is None:
            hour = h
        if minute is None:
            minute = m
        if second is None:
            second = s
        if microsecond is None:
            microsecond = us
        if tzinfo is True:
            tzinfo = tz
        return time(hour, minute, second, microsecond, tzinfo)

    def isoformat(self, timespec="auto"):
        return self._format(timespec, None)

    def _format(self, ts, dt):
        s = self._td._format(_TIME_SPEC.index(ts))
        if self._tz is not None:
            s += self._tz.isoformat(dt)
        return s

    def __repr__(self):
        return "datetime.time(microsecond={}, tzinfo={})".format(self._td._us, repr(self._tz))

    __str__ = isoformat

    def __bool__(self):
        return True

    def __eq__(self, other):
        return self._td == other._td and self._tz == other._tz

    def __hash__(self):
        if not hasattr(self, "_hash"):
            self._hash = hash((self._td, self._tz))
        return self._hash

    def utcoffset(self):
        return None if self._tz is None else self._tz.utcoffset(None)

    def dst(self):
        return None if self._tz is None else self._tz.dst(None)

    def tzname(self):
        return None if self._tz is None else self._tz.tzname(None)

    def tuple(self):
        d, h, m, s, us = self._td.tuple()
        return h, m, s, us, self._tz


time.min = time(0)
time.max = time(23, 59, 59, 999_999)
time.resolution = timedelta.resolution


class date:
    def __init__(self, year, month, day):
        if (
            MINYEAR <= year <= MAXYEAR
            and 1 <= month <= 12
            and 1 <= day <= _days_in_month(year, month)
        ):
            self._ord = _ymd2ord(year, month, day)
        elif year == 0 and month == 0 and 1 <= day <= 3_652_059:
            self._ord = day
        else:
            raise ValueError

    @staticmethod
    def today():
        return datetime.today().date()

    @staticmethod
    def fromordinal(n):
        return date(0, 0, n)

    @staticmethod
    def fromisoformat(s):
        if len(s) < 10 or s[4] != "-" or s[7] != "-":
            raise ValueError
        y = int(s[0:4])
        m = int(s[5:7])
        d = int(s[8:10])
        return date(y, m, d)

    @property
    def year(self):
        return self.tuple()[0]

    @property
    def month(self):
        return self.tuple()[1]

    @property
    def day(self):
        return self.tuple()[2]

    def toordinal(self):
        return self._ord

    def replace(self, year=None, month=None, day=None):
        year_, month_, day_ = self.tuple()
        if year is None:
            year = year_
        if month is None:
            month = month_
        if day is None:
            day = day_
        return date(year, month, day)

    def __add__(self, other):
        return date.fromordinal(self._ord + other.days)

    def __sub__(self, other):
        if isinstance(other, date):
            return timedelta(days=self._ord - other._ord)
        else:
            return date.fromordinal(self._ord - other.days)

    def __eq__(self, other):
        return self._ord == other._ord

    def __le__(self, other):
        return self._ord <= other._ord

    def __lt__(self, other):
        return self._ord < other._ord

    def __ge__(self, other):
        return self._ord >= other._ord

    def __gt__(self, other):
        return self._ord > other._ord

    def weekday(self):
        return (self._ord + 6) % 7

    def isoweekday(self):
        return self._ord % 7 or 7

    def tuple(self):
        return _ord2ymd(self._ord)

    def isoformat(self):
        return "%04d-%02d-%02d" % self.tuple()

    def __repr__(self):
        return "datetime.date(0, 0, {})".format(self._ord)

    __str__ = isoformat

    def __hash__(self):
        if not hasattr(self, "_hash"):
            self._hash = hash(self._ord)
        return self._hash


date.min = date(MINYEAR, 1, 1)
date.max = date(MAXYEAR, 12, 31)
date.resolution = timedelta(days=1)


class datetime:
    def __init__(self, year, month, day, hour=0, minute=0, second=0, microsecond=0, tzinfo=None):
        self._date = date(year, month, day)
        self._time = time(hour, minute, second, microsecond, tzinfo)

    @staticmethod
    def today():
        return datetime.now()

    @staticmethod
    def now(tz=None):
        return datetime(*_time.localtime()[:6], tzinfo=tz)

    @staticmethod
    def fromisoformat(s):
        d = date.fromisoformat(s)
        t = time.fromisoformat(s[11:]) if len(s) > 12 else time()
        return datetime.combine(d, t)

    @staticmethod
    def combine(date, time, tzinfo_=None):
        return datetime(0, 0, date.toordinal(), 0, 0, 0, time._td._us, tzinfo_ or time._tz)

    @property
    def year(self):
        return self._date.year

    @property
    def month(self):
        return self._date.month

    @property
    def day(self):
        return self._date.day

    @property
    def hour(self):
        return self._time.hour

    @property
    def minute(self):
        return self._time.minute

    @property
    def second(self):
        return self._time.second

    @property
    def microsecond(self):
        return self._time.microsecond

    @property
    def tzinfo(self):
        return self._time._tz

    def __add__(self, other):
        us = self._time._td._us + other._us
        d, us = divmod(us, 86_400_000_000)
        d += self._date._ord
        return datetime(0, 0, d, 0, 0, 0, us, self._time._tz)

    def __sub__(self, other):
        if isinstance(other, timedelta):
            return self.__add__(-other)
        elif isinstance(other, datetime):
            d, us = self._sub(other)
            return timedelta(d, 0, us)
        else:
            raise TypeError

    def _sub(self, other):
        # Subtract two datetime instances.
        if (self._time._tz == None) ^ (other._time._tz == None):
            raise TypeError
        if self._time._tz == None or self.utcoffset() == other.utcoffset():
            dt1 = self
            dt2 = other
        else:
            dt1 = self.astimezone(timezone.utc)
            dt2 = other.astimezone(timezone.utc)
        D = dt1._date._ord - dt2._date._ord
        us = dt1._time._td._us - dt2._time._td._us
        d, us = divmod(us, 86_400_000_000)
        return D + d, us

    def __eq__(self, other):
        if (self._time._tz == None) ^ (other._time._tz == None):
            return False
        return self._cmp(other) == 0

    def __le__(self, other):
        return self._cmp(other) <= 0

    def __lt__(self, other):
        return self._cmp(other) < 0

    def __ge__(self, other):
        return self._cmp(other) >= 0

    def __gt__(self, other):
        return self._cmp(other) > 0

    def _cmp(self, other):
        # Compare two datetime instances.
        d, us = self._sub(other)
        if d < 0:
            return -1
        if d > 0:
            return 1

        if us < 0:
            return -1
        if us > 0:
            return 1

        return 0

    def date(self):
        return date.fromordinal(self._date._ord)

    def time(self):
        return time(microsecond=self._time._td._us)

    def timetz(self):
        return time(microsecond=self._time._td._us, tzinfo=self._time._tz)

    def replace(
        self,
        year=None,
        month=None,
        day=None,
        hour=None,
        minute=None,
        second=None,
        microsecond=None,
        tzinfo=True,
    ):
        Y, M, D, h, m, s, us, tz = self.tuple()
        if year is None:
            year = Y
        if month is None:
            month = M
        if day is None:
            day = D
        if hour is None:
            hour = h
        if minute is None:
            minute = m
        if second is None:
            second = s
        if microsecond is None:
            microsecond = us
        if tzinfo is True:
            tzinfo = tz
        return datetime(year, month, day, hour, minute, second, microsecond, tzinfo)

    def astimezone(self, tz):
        if self._time._tz is None:
            raise NotImplementedError
        if self._time._tz is tz:
            return self
        utc = self - self._time._tz.utcoffset(self)
        utc = utc.replace(tzinfo=tz)
        return tz.fromutc(utc)

    def utcoffset(self):
        return None if self._time._tz is None else self._time._tz.utcoffset(self)

    def dst(self):
        return None if self._time._tz is None else self._time._tz.dst(self)

    def tzname(self):
        return None if self._time._tz is None else self._time._tz.tzname(self)

    def timetuple(self):
        if self._time._tz is None:
            epoch = datetime.EPOCH.replace(tzinfo=None)
            return _time.gmtime(round((self - epoch).total_seconds()))
        else:
            return _time.localtime(round((self - datetime.EPOCH).total_seconds()))

    def toordinal(self):
        return self._date._ord

    def timestamp(self):
        return (self - datetime.EPOCH).total_seconds()

    def weekday(self):
        return self._date.weekday()

    def isoweekday(self):
        return self._date.isoweekday()

    def isoformat(self, sep="T", timespec="auto"):
        return self._date.isoformat() + sep + self._time._format(timespec, self)

    def __repr__(self):
        Y, M, D, h, m, s, us, tz = self.tuple()
        tz = repr(tz)
        return "datetime.datetime({}, {}, {}, {}, {}, {}, {}, {})".format(Y, M, D, h, m, s, us, tz)

    def __str__(self):
        return self.isoformat(" ")

    def __hash__(self):
        if not hasattr(self, "_hash"):
            self._hash = hash((self._date, self._time))
        return self._hash

    def tuple(self):
        return self._date.tuple() + self._time.tuple()


datetime.EPOCH = datetime(*_time.gmtime(0)[:6], tzinfo=timezone.utc)
