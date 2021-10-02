# datetime.py

__version__ = "2.0.0"

# The following functions were (stolen and) adapted from Python's datetime.
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
    return (0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)[month]


def _days_before_month(year, month):
    # year, month -> number of days in year preceding first day of month.
    return (0, 0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334)[month] + (
        month > 2 and _is_leap(year)
    )


def _ymd2ord(year, month, day):
    # year, month, day -> ordinal, considering 01-Jan-0001 as day 1.
    return _days_before_year(year) + _days_before_month(year, month) + day


def _ord2ymd(n):
    # ordinal -> (year, month, day), considering 01-Jan-0001 as day 1.
    n -= 1
    n400, n = divmod(n, 146097)
    year = n400 * 400 + 1
    n100, n = divmod(n, 36524)
    n4, n = divmod(n, 1461)
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


class timedelta:
    MINYEAR = -68   # timedelta( 0,  0,  0, -365*68).total_seconds() >= -2**31
    MAXYEAR = 68    # timedelta(23, 59, 59,  365*68).total_seconds() <=  2**31 - 1

    def __init__(self, hours=0, minutes=0, seconds=0, days=0, weeks=0):
        self._s = round((((weeks * 7 + days) * 24 + hours) * 60 + minutes) * 60 + seconds)

    def total_seconds(self):
        return self._s

    def __add__(self, other):
        if isinstance(other, datetime):
            return other + self
        return timedelta(seconds=self._s + other._s)

    def __sub__(self, other):
        return timedelta(seconds=self._s - other._s)

    def __mul__(self, other):
        return timedelta(seconds=round(other * self._s))

    __rmul__ = __mul__

    def __truediv__(self, other):
        if isinstance(other, timedelta):
            return self._s / other._s
        else:
            return timedelta(seconds=round(self._s / other))

    def __floordiv__(self, other):
        if isinstance(other, timedelta):
            return self._s // other._s
        else:
            return timedelta(seconds=int(self._s // other))

    def __mod__(self, other):
        return timedelta(seconds=self._s % other._s)

    def __divmod__(self, other):
        q, r = divmod(self._s, other._s)
        return q, timedelta(seconds=r)

    def __neg__(self):
        return timedelta(seconds=-self._s)

    def __pos__(self):
        return self

    def __eq__(self, other):
        return self._s == other._s

    def __le__(self, other):
        return self._s <= other._s

    def __lt__(self, other):
        return self._s < other._s

    def __ge__(self, other):
        return self._s >= other._s

    def __gt__(self, other):
        return self._s > other._s

    def __bool__(self):
        return self._s != 0

    def __neg__(self):
        return timedelta(seconds=-self._s)

    def __pos__(self):
        return self

    def __abs__(self):
        return timedelta(seconds=abs(self._s))

    def __repr__(self):
        return "datetime.timedelta(seconds=%d)" % self._s

    def __str__(self):
        return self.isoformat()

    def isoformat(self):
        t = self.tuple()
        if 0 <= self._s < 86400:
            return "%02d:%02d:%02d" % t[2:]
        else:
            return "%s%dd %02d:%02d:%02d" % t

    def tuple(self, sign_pos=""):
        s = self._s
        if s < 0:
            s *= -1
            g = "-"
        else:
            g = sign_pos
        m, s = divmod(s, 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)
        return g, d, h, m, s


timedelta.min = timedelta(seconds=-2147483648)  # -2**31
timedelta.max = timedelta(seconds=2147483647)  #  2**31 - 1
timedelta.resolution = timedelta(seconds=1)


class timezone:
    def __init__(self, offset, name=None):
        if not (timedelta(hours=-24) < offset < timedelta(hours=24)):
            raise ValueError
        self._offset = offset
        self._name = name

    def __str__(self):
        return self.tzname(None)

    def utcoffset(self, dt):
        dst = self.dst(dt)
        if dst is None or not dst:
            return self._offset
        return self._offset + dst

    def dst(self, dt):
        return None

    def tzname(self, dt):
        if self._name != None:
            return self._name
        return self.isoformat(dt)

    def isoformat(self, dt, *, utc=True):
        td = self.utcoffset(dt)
        if utc and not td:
            return "UTC"
        sign, day, hour, minute, second = td.tuple("+")
        return "%s%s%02d:%02d" % ("UTC" if utc else "", sign, hour, minute)


timezone.utc = timezone(timedelta(0))


class datetime:
    MINYEAR = 1
    MAXYEAR = 9999

    def __init__(self, year, month, day, hour=0, minute=0, second=0, tzinfo=None):
        if year == 0 and month == 0 and day > 0:
            self._ord = day
        elif (
            self.MINYEAR <= year <= self.MAXYEAR
            and 1 <= month <= 12
            and 1 <= day <= _days_in_month(year, month)
            and 0 <= hour < 24
            and 0 <= minute < 60
            and 0 <= second < 60
        ):
            self._ord = _ymd2ord(year, month, day)
        else:
            raise ValueError
        self._time = timedelta(hour, minute, second)
        self._tz = tzinfo

    def __add__(self, other):
        time = self._time + other
        sign, days, hour, minute, second = time.tuple()
        if sign == "-":
            days += 1
            time += timedelta(days=days)
            days = -days
        year, month, day, hour, minute, second, tz = self._tuple(self._ord + days, time, self._tz)[:7]
        return datetime(year, month, day, hour, minute, second, tz)

    def __sub__(self, other):
        if isinstance(other, timedelta):
            return self + -other
        elif isinstance(other, datetime):
            days, time = self._sub(other)
            return time + timedelta(days=days)
        else:
            raise TypeError

    def __lt__(self, other):
        return self._cmp(other) < 0

    def __le__(self, other):
        return self._cmp(other) <= 0

    def __eq__(self, other):
        return self._cmp(other) == 0

    def __ge__(self, other):
        return self._cmp(other) >= 0

    def __gt__(self, other):
        return self._cmp(other) > 0

    def __repr__(self):
        return "datetime.datetime(days=%d, seconds=%d, tzinfo=%s)" \
                % (self._ord, self._time._s, repr(self._tz))

    def __str__(self):
        return self.isoformat(" ")

    @property
    def tzinfo(self):
        return self._tz

    def utcoffset(self):
        return None if self._tz is None else self._tz.utcoffset(self)

    def dst(self):
        return None if self._tz is None else self._tz.dst(self)

    def date(self):
        return datetime(0, 0, self.toordinal(), tzinfo=self._tz)

    def time(self):
        return timedelta(seconds=self._time.total_seconds())

    def tzname(self):
        return None if self._tz is None else self._tz.tzname(self)

    def replace(
        self, year=None, month=None, day=None, hour=None, minute=None, second=None, tzinfo=True
    ):
        year_, month_, day_, hour_, minute_, second_, tz_ = self.tuple()
        if year is None:
            year = year_
        if month is None:
            month = month_
        if day is None:
            day = day_
        if hour is None:
            hour = hour_
        if minute is None:
            minute = minute_
        if second is None:
            second = second_
        if tzinfo is True:
            tzinfo = tz_
        return datetime(year, month, day, hour, minute, second, tzinfo)

    def astimezone(self, tz):
        if self._tz == None:
            raise NotImplementedError
        ret = self - self.utcoffset() + tz.utcoffset(self)
        return ret.replace(tzinfo=tz)

    def dateisoformat(self):
        return self.isoformat()[:10]

    def timeisoformat(self):
        return self.isoformat()[11:19]

    def isoformat(self, sep="T"):
        dt = ("%04d-%02d-%02d" + sep + "%02d:%02d:%02d") % self.tuple()[:6]
        if self._tz == None:
            return dt
        return dt + self._tz.isoformat(self, utc=False)

    def toordinal(self):
        return self._ord

    def isoweekday(self):
        return self._ord % 7 or 7

    def tuple(self):
        return self._tuple(self._ord, self._time, self._tz)[:-2]

    def _sub(self, other):
        # Subtract two datetime instances.
        if (self._tz == None) ^ (other._tz == None):
            raise TypeError

        if self._tz == None or self.utcoffset() == other.utcoffset():
            dt1 = self
            dt2 = other
        else:
            dt1 = self.astimezone(timezone.utc)
            dt2 = other.astimezone(timezone.utc)

        days = dt1._ord - dt2._ord
        time = dt1._time - dt2._time
        return days, time

    def _cmp(self, other):
        # Compare two datetime instances.
        days, time = self._sub(other)
        if days < 0:
            return -1
        if days > 0:
            return 1

        secs = time.total_seconds()
        if secs < 0:
            return -1
        if secs > 0:
            return 1

        return 0

    def _tuple(self, ordinal, time, tz):
        # Split a datetime to its components.
        year, month, day = _ord2ymd(ordinal)
        sign, days, hour, minute, second = time.tuple()
        return year, month, day, hour, minute, second, tz, days, sign


def fromisoformat(s):
    l = len(s)
    if l < 10 or s[4] != "-" or s[7] != "-":
        raise ValueError
    # parse date
    year = int(s[0:4])
    month = int(s[5:7])
    day = int(s[8:10])
    hour = 0
    minute = 0
    second = 0
    microsecond = 0
    tz_sign = ""
    tz_hour = 0
    tz_minute = 0
    tz_second = 0
    tz_microsecond = 0
    i = 10
    if l > i and s[i] != "+":
        # parse time
        if l - i < 3:
            raise ValueError
        i += 3
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
                second = int(s[i - 2 : i])
                if l > i and s[i] == ".":
                    i += 4
                    if l - i < 0:
                        raise ValueError
                    microsecond = 1000 * int(s[i - 3 : i])
                    if l > i and s[i] != "+":
                        i += 3
                        if l - i < 0:
                            raise ValueError
                        microsecond += int(s[i - 3 : i])
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
            tz_second = int(s[i - 2 : i])
            if l > i and s[i] == ".":
                i += 7
                if l - i < 0:
                    raise ValueError
                tz_microsecond = int(s[i - 6 : i])
    if l != i:
        raise ValueError
    if tz_sign:
        td = timedelta(tz_hour, tz_minute, tz_second)
        if tz_sign == "-":
            td = -td
        tz = timezone(td)
    else:
        tz = None
    return datetime(year, month, day, hour, minute, second, tz)


def fromordinal(n):
    if not 1 <= n <= 3652059:
        raise ValueError
    return datetime(0, 0, n)


def combine(date, time, tzinfo=True):
    if tzinfo is True:
        dt = date
    else:
        dt = date.replace(tzinfo=tzinfo)
    return dt + time
