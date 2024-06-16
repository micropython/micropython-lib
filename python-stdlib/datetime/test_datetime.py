# See https://github.com/python/cpython/blob/3.9/Lib/test/datetimetester.py
#
# This script can be run in 3 different modes:
# 1. `python3 test_datetime.py --stdlib`: checks that the tests comply to
#    CPython's standard datetime library.
# 2. `python3 test_datetime.py`: runs the tests against datetime.py, using
#    CPython's standard unittest (which accepts filter options, such as
#    `-v TestTimeDelta -k tuple`, and provides more verbose output in case
#    of failure).
# 3. `micropython test_datetime.py`: runs the tests against datetime.py
#    using MicroPython's unittest library (which must be available).
#
# This script also accepts option `--reorder` which rewrites this file
# in-place by numbering tests in sequence.

import sys

STDLIB = False

if __name__ == "__main__":
    while len(sys.argv) > 1:
        if sys.argv[1] == "--reorder":
            import fileinput, re

            with fileinput.input(files=sys.argv[0], inplace=True) as f:
                cases = {}
                n = 0
                for line in f:
                    match = re.match("(\s+def\s+test_)(\w+?)(?:\d+)(\(.+\):)", line)
                    if match:
                        prefix, name, suffix = match.groups()
                        if name != last_name:
                            if name in cases[case]:
                                sys.exit(
                                    f"duplicated test in {case} at line {fileinput.filelineno()}: {name}"
                                )
                            cases[case].append(name)
                            last_name = name
                            i = 0
                        print(f"{prefix}{name}{i:02d}{suffix}")
                        i += 1
                        n += 1
                        continue

                    match = re.match("class\s+(Test[\w\d]+)\(", line)
                    if match:
                        case = match[1]
                        if case in cases:
                            sys.exit(
                                f"duplicated test case at line {fileinput.filelineno()}: {case}"
                            )
                        cases[case] = []
                        last_name = ""

                    print(line, end="")
            print(f"Reordered {n} tests in {len(cases)} cases")
        elif sys.argv[1] == "--stdlib":
            sys.path.pop(0)
            STDLIB = True
        else:
            break
        sys.argv.pop(1)

import os
import time as mod_time
import datetime as mod_datetime
from datetime import MAXYEAR, MINYEAR, datetime, date, time, timedelta, timezone, tzinfo
import unittest


# See localtz.patch
try:
    datetime.fromtimestamp(0)
    LOCALTZ = True
except NotImplementedError:
    LOCALTZ = False


if hasattr(datetime, "EPOCH"):
    EPOCH = datetime.EPOCH
else:
    EPOCH = datetime(*mod_time.gmtime(0)[:6], tzinfo=timezone.utc)


def eval_mod(s):
    return eval(s.replace("datetime.", "mod_datetime."))


### timedelta ################################################################

a = timedelta(hours=7)
b = timedelta(minutes=6)
c = timedelta(seconds=10)
us = timedelta(microseconds=1)
td0 = timedelta(0)
td1 = timedelta(2, 3, 4)
td2 = timedelta(2, 3, 4)
td3 = timedelta(2, 3, 5)
td4 = timedelta(
    days=100,
    weeks=-7,
    hours=-24 * (100 - 49),
    minutes=-3,
    seconds=12,
    microseconds=(3 * 60 - 12) * 1000000,
)  # == timedelta(0)

td1h = timedelta(hours=1)
td1hr = "datetime.timedelta(microseconds={})".format(1 * 3600 * 10**6)
td10h2m = timedelta(hours=10, minutes=2)
td10h2mr = "datetime.timedelta(microseconds={})".format((10 * 3600 + 2 * 60) * 10**6)
tdn10h2m40s = timedelta(hours=-10, minutes=2, seconds=40)
tdn10h2m40sr = "datetime.timedelta(microseconds={})".format((-10 * 3600 + 2 * 60 + 40) * 10**6)
td1h2m40s100us = timedelta(hours=1, minutes=2, seconds=40, microseconds=100)
td1h2m40s100usr = "datetime.timedelta(microseconds={})".format(
    (1 * 3600 + 2 * 60 + 40) * 10**6 + 100
)


class Test0TimeDelta(unittest.TestCase):
    def test___init__00(self):
        self.assertEqual(timedelta(), timedelta(weeks=0, days=0, hours=0, minutes=0, seconds=0))

    def test___init__01(self):
        self.assertEqual(timedelta(weeks=1), timedelta(days=7))

    def test___init__02(self):
        self.assertEqual(timedelta(days=1), timedelta(hours=24))

    def test___init__03(self):
        self.assertEqual(timedelta(hours=1), timedelta(minutes=60))

    def test___init__04(self):
        self.assertEqual(timedelta(minutes=1), timedelta(seconds=60))

    def test___init__05(self):
        self.assertEqual(timedelta(seconds=1), timedelta(milliseconds=1000))

    def test___init__06(self):
        self.assertEqual(timedelta(milliseconds=1), timedelta(microseconds=1000))

    def test___init__07(self):
        self.assertEqual(timedelta(weeks=1.0 / 7), timedelta(days=1))

    def test___init__08(self):
        self.assertEqual(timedelta(days=1.0 / 24), timedelta(hours=1))

    def test___init__09(self):
        self.assertEqual(timedelta(hours=1.0 / 60), timedelta(minutes=1))

    def test___init__10(self):
        self.assertEqual(timedelta(minutes=1.0 / 60), timedelta(seconds=1))

    def test___init__11(self):
        self.assertEqual(timedelta(seconds=0.001), timedelta(milliseconds=1))

    def test___init__12(self):
        self.assertEqual(timedelta(milliseconds=0.001), timedelta(microseconds=1))

    def test___init__13(self):
        self.assertEqual(td1h, eval_mod(td1hr))

    def test___init__14(self):
        self.assertEqual(td10h2m, eval_mod(td10h2mr))

    def test___init__15(self):
        self.assertEqual(tdn10h2m40s, eval_mod(tdn10h2m40sr))

    def test___init__16(self):
        self.assertEqual(td1h2m40s100us, eval_mod(td1h2m40s100usr))

    @unittest.skipIf(STDLIB, "standard datetime differs")
    def test___repr__00(self):
        self.assertEqual(repr(td1h), td1hr)

    @unittest.skipIf(STDLIB, "standard datetime differs")
    def test___repr__01(self):
        self.assertEqual(repr(td10h2m), td10h2mr)

    @unittest.skipIf(STDLIB, "standard datetime differs")
    def test___repr__02(self):
        self.assertEqual(repr(tdn10h2m40s), tdn10h2m40sr)

    @unittest.skipIf(STDLIB, "standard datetime differs")
    def test___repr__03(self):
        self.assertEqual(repr(td1h2m40s100us), td1h2m40s100usr)

    def test___repr__04(self):
        self.assertEqual(td1, eval_mod(repr(td1)))

    def test_total_seconds00(self):
        d = timedelta(days=365)
        self.assertEqual(d.total_seconds(), 31536000.0)

    def test_days00(self):
        self.assertEqual(td1.days, 2)

    def test_seconds00(self):
        self.assertEqual(td1.seconds, 3)

    def test_microseconds00(self):
        self.assertEqual(td1.microseconds, 4)

    def test___add__00(self):
        self.assertEqual(a + b + c, timedelta(hours=7, minutes=6, seconds=10))

    def test___add__01(self):
        dt = a + datetime(2010, 1, 1, 12, 30)
        self.assertEqual(dt, datetime(2010, 1, 1, 12 + 7, 30))

    def test___sub__00(self):
        self.assertEqual(a - b, timedelta(hours=6, minutes=60 - 6))

    def test___neg__00(self):
        self.assertEqual(-a, timedelta(hours=-7))

    def test___neg__01(self):
        self.assertEqual(-b, timedelta(hours=-1, minutes=54))

    def test___neg__02(self):
        self.assertEqual(-c, timedelta(hours=-1, minutes=59, seconds=50))

    def test___pos__00(self):
        self.assertEqual(+a, timedelta(hours=7))

    def test___abs__00(self):
        self.assertEqual(abs(a), a)

    def test___abs__01(self):
        self.assertEqual(abs(-a), a)

    def test___mul__00(self):
        self.assertEqual(a * 10, timedelta(hours=70))

    def test___mul__01(self):
        self.assertEqual(a * 10, 10 * a)

    def test___mul__02(self):
        self.assertEqual(b * 10, timedelta(minutes=60))

    def test___mul__03(self):
        self.assertEqual(10 * b, timedelta(minutes=60))

    def test___mul__04(self):
        self.assertEqual(c * 10, timedelta(seconds=100))

    def test___mul__05(self):
        self.assertEqual(10 * c, timedelta(seconds=100))

    def test___mul__06(self):
        self.assertEqual(a * -1, -a)

    def test___mul__07(self):
        self.assertEqual(b * -2, -b - b)

    def test___mul__08(self):
        self.assertEqual(c * -2, -c + -c)

    def test___mul__09(self):
        self.assertEqual(b * (60 * 24), (b * 60) * 24)

    def test___mul__10(self):
        self.assertEqual(b * (60 * 24), (60 * b) * 24)

    def test___mul__11(self):
        self.assertEqual(c * 6, timedelta(minutes=1))

    def test___mul__12(self):
        self.assertEqual(6 * c, timedelta(minutes=1))

    def test___truediv__00(self):
        self.assertEqual(a / 0.5, timedelta(hours=14))

    def test___truediv__01(self):
        self.assertEqual(b / 0.5, timedelta(minutes=12))

    def test___truediv__02(self):
        self.assertEqual(a / 7, timedelta(hours=1))

    def test___truediv__03(self):
        self.assertEqual(b / 6, timedelta(minutes=1))

    def test___truediv__04(self):
        self.assertEqual(c / 10, timedelta(seconds=1))

    def test___truediv__05(self):
        self.assertEqual(a / 10, timedelta(minutes=7 * 6))

    def test___truediv__06(self):
        self.assertEqual(a / 3600, timedelta(seconds=7))

    def test___truediv__07(self):
        self.assertEqual(a / a, 1.0)

    def test___truediv__08(self):
        t = timedelta(hours=1, minutes=24, seconds=19)
        second = timedelta(seconds=1)
        self.assertEqual(t / second, 5059.0)

    def test___truediv__09(self):
        t = timedelta(minutes=2, seconds=30)
        minute = timedelta(minutes=1)
        self.assertEqual(t / minute, 2.5)

    def test___floordiv__00(self):
        self.assertEqual(a // 7, timedelta(hours=1))

    def test___floordiv__01(self):
        self.assertEqual(b // 6, timedelta(minutes=1))

    def test___floordiv__02(self):
        self.assertEqual(c // 10, timedelta(seconds=1))

    def test___floordiv__03(self):
        self.assertEqual(a // 10, timedelta(minutes=7 * 6))

    def test___floordiv__04(self):
        self.assertEqual(a // 3600, timedelta(seconds=7))

    def test___floordiv__05(self):
        t = timedelta(hours=1, minutes=24, seconds=19)
        second = timedelta(seconds=1)
        self.assertEqual(t // second, 5059)

    def test___floordiv__06(self):
        t = timedelta(minutes=2, seconds=30)
        minute = timedelta(minutes=1)
        self.assertEqual(t // minute, 2)

    def test___mod__00(self):
        t = timedelta(minutes=2, seconds=30)
        r = t % timedelta(minutes=1)
        self.assertEqual(r, timedelta(seconds=30))

    def test___mod__01(self):
        t = timedelta(minutes=-2, seconds=30)
        r = t % timedelta(minutes=1)
        self.assertEqual(r, timedelta(seconds=30))

    def test___divmod__00(self):
        t = timedelta(minutes=2, seconds=30)
        q, r = divmod(t, timedelta(minutes=1))
        self.assertEqual(q, 2)
        self.assertEqual(r, timedelta(seconds=30))

    def test___divmod__01(self):
        t = timedelta(minutes=-2, seconds=30)
        q, r = divmod(t, timedelta(minutes=1))
        self.assertEqual(q, -2)
        self.assertEqual(r, timedelta(seconds=30))

    def test___eq__00(self):
        self.assertEqual(td1, td2)

    def test___eq__01(self):
        self.assertTrue(not td1 != td2)

    def test___eq__02(self):
        self.assertEqual(timedelta(hours=6, minutes=60), a)

    def test___eq__03(self):
        self.assertEqual(timedelta(seconds=60 * 6), b)

    def test___eq__04(self):
        self.assertTrue(not td1 == td3)

    def test___eq__05(self):
        self.assertTrue(td1 != td3)

    def test___eq__06(self):
        self.assertTrue(td3 != td1)

    def test___eq__07(self):
        self.assertTrue(not td3 == td1)

    def test___le__00(self):
        self.assertTrue(td1 <= td2)

    def test___le__01(self):
        self.assertTrue(td1 <= td3)

    def test___le__02(self):
        self.assertTrue(not td3 <= td1)

    def test___lt__00(self):
        self.assertTrue(not td1 < td2)

    def test___lt__01(self):
        self.assertTrue(td1 < td3)

    def test___lt__02(self):
        self.assertTrue(not td3 < td1)

    def test___ge__00(self):
        self.assertTrue(td1 >= td2)

    def test___ge__01(self):
        self.assertTrue(td3 >= td1)

    def test___ge__02(self):
        self.assertTrue(not td1 >= td3)

    def test___gt__00(self):
        self.assertTrue(not td1 > td2)

    def test___gt__01(self):
        self.assertTrue(td3 > td1)

    def test___gt__02(self):
        self.assertTrue(not td1 > td3)

    def test___bool__00(self):
        self.assertTrue(timedelta(hours=1))

    def test___bool__01(self):
        self.assertTrue(timedelta(minutes=1))

    def test___bool__02(self):
        self.assertTrue(timedelta(seconds=1))

    def test___bool__03(self):
        self.assertTrue(not td0)

    def test___str__00(self):
        self.assertEqual(str(timedelta(days=1)), "1 day, 0:00:00")

    def test___str__01(self):
        self.assertEqual(str(timedelta(days=-1)), "-1 day, 0:00:00")

    def test___str__02(self):
        self.assertEqual(str(timedelta(days=2)), "2 days, 0:00:00")

    def test___str__03(self):
        self.assertEqual(str(timedelta(days=-2)), "-2 days, 0:00:00")

    def test___str__04(self):
        self.assertEqual(str(timedelta(hours=12, minutes=58, seconds=59)), "12:58:59")

    def test___str__05(self):
        self.assertEqual(str(timedelta(hours=2, minutes=3, seconds=4)), "2:03:04")

    def test___hash__00(self):
        self.assertEqual(td0, td4)
        self.assertEqual(hash(td0), hash(td4))

    def test___hash__01(self):
        tt0 = td0 + timedelta(weeks=7)
        tt4 = td4 + timedelta(days=7 * 7)
        self.assertEqual(hash(tt0), hash(tt4))

    def test___hash__02(self):
        d = {td0: 1}
        d[td4] = 2
        self.assertEqual(len(d), 1)
        self.assertEqual(d[td0], 2)

    def test_constant00(self):
        self.assertIsInstance(timedelta.min, timedelta)
        self.assertIsInstance(timedelta.max, timedelta)
        self.assertIsInstance(timedelta.resolution, timedelta)
        self.assertTrue(timedelta.max > timedelta.min)

    def test_constant01(self):
        self.assertEqual(timedelta.min, timedelta(days=-999_999_999))

    def test_constant02(self):
        self.assertEqual(
            timedelta.max,
            timedelta(days=999_999_999, seconds=24 * 3600 - 1, microseconds=10**6 - 1),
        )

    def test_constant03(self):
        self.assertEqual(timedelta.resolution, timedelta(microseconds=1))

    def test_computation00(self):
        self.assertEqual((3 * us) * 0.5, 2 * us)

    def test_computation01(self):
        self.assertEqual((5 * us) * 0.5, 2 * us)

    def test_computation02(self):
        self.assertEqual(0.5 * (3 * us), 2 * us)

    def test_computation03(self):
        self.assertEqual(0.5 * (5 * us), 2 * us)

    def test_computation04(self):
        self.assertEqual((-3 * us) * 0.5, -2 * us)

    def test_computation05(self):
        self.assertEqual((-5 * us) * 0.5, -2 * us)

    def test_computation06(self):
        self.assertEqual((3 * us) / 2, 2 * us)

    def test_computation07(self):
        self.assertEqual((5 * us) / 2, 2 * us)

    def test_computation08(self):
        self.assertEqual((-3 * us) / 2.0, -2 * us)

    def test_computation09(self):
        self.assertEqual((-5 * us) / 2.0, -2 * us)

    def test_computation10(self):
        self.assertEqual((3 * us) / -2, -2 * us)

    def test_computation11(self):
        self.assertEqual((5 * us) / -2, -2 * us)

    def test_computation12(self):
        self.assertEqual((3 * us) / -2.0, -2 * us)

    def test_computation13(self):
        self.assertEqual((5 * us) / -2.0, -2 * us)

    def test_computation14(self):
        for i in range(-10, 10):
            # with self.subTest(i=i): not supported by Micropython
            self.assertEqual((i * us / 3) // us, round(i / 3))

    def test_computation15(self):
        for i in range(-10, 10):
            # with self.subTest(i=i): not supported by Micropython
            self.assertEqual((i * us / -3) // us, round(i / -3))

    def test_carries00(self):
        td1 = timedelta(
            days=100,
            weeks=-7,
            hours=-24 * (100 - 49),
            minutes=-3,
            seconds=3 * 60 + 1,
        )
        td2 = timedelta(seconds=1)
        self.assertEqual(td1, td2)

    def test_resolution00(self):
        self.assertIsInstance(timedelta.min, timedelta)

    def test_resolution01(self):
        self.assertIsInstance(timedelta.max, timedelta)

    def test_resolution02(self):
        self.assertIsInstance(timedelta.resolution, timedelta)

    def test_resolution03(self):
        self.assertTrue(timedelta.max > timedelta.min)

    def test_resolution04(self):
        self.assertEqual(timedelta.resolution, timedelta(microseconds=1))

    @unittest.skipIf(STDLIB, "standard timedelta has no tuple()")
    def test_tuple00(self):
        self.assertEqual(td1.tuple(), (2, 0, 0, 3, 4))

    @unittest.skipIf(STDLIB, "standard timedelta has no tuple()")
    def test_tuple01(self):
        self.assertEqual(td1h2m40s100us.tuple(), (0, 1, 2, 40, 100))


### timezone #################################################################


class Cet(tzinfo):
    # Central European Time (see https://en.wikipedia.org/wiki/Summer_time_in_Europe)

    def utcoffset(self, dt):
        h = 2 if self.isdst(dt)[0] else 1
        return timedelta(hours=h)

    def dst(self, dt):
        h = 1 if self.isdst(dt)[0] else 0
        return timedelta(hours=h)

    def tzname(self, dt):
        return "CEST" if self.isdst(dt)[0] else "CET"

    def fromutc(self, dt):
        assert dt.tzinfo is self
        isdst, fold = self.isdst(dt, utc=True)
        h = 2 if isdst else 1
        dt += timedelta(hours=h)
        dt = dt.replace(fold=fold)
        return dt

    def isdst(self, dt, utc=False):
        if dt is None:
            return False, None

        year = dt.year
        if not 2000 <= year < 2100:
            # Formulas below are valid in the range [2000; 2100)
            raise ValueError

        hour = 1 if utc else 3
        day = 31 - (5 * year // 4 + 4) % 7  # last Sunday of March
        beg = datetime(year, 3, day, hour)
        day = 31 - (5 * year // 4 + 1) % 7  # last Sunday of October
        end = datetime(year, 10, day, hour)

        dt = dt.replace(tzinfo=None)
        if utc:
            fold = 1 if end <= dt < end + timedelta(hours=1) else 0
        else:
            fold = dt.fold
        isdst = beg <= dt < end
        return isdst, fold

    def __repr__(self):
        return "Cet()"

    def __str__(self):
        return self.tzname(None)

    def __eq__(self, other):
        return repr(self) == repr(other)

    def __hash__(self):
        return hash(repr(self))


class USTimeZone(tzinfo):
    DSTSTART = datetime(1, 3, 8, 2)
    DSTEND = datetime(1, 11, 1, 2)
    ZERO = timedelta(0)
    HOUR = timedelta(hours=1)

    def __init__(self, hours, reprname, stdname, dstname):
        self.stdoffset = timedelta(hours=hours)
        self.reprname = reprname
        self.stdname = stdname
        self.dstname = dstname

    def __repr__(self):
        return self.reprname

    def tzname(self, dt):
        if self.dst(dt):
            return self.dstname
        else:
            return self.stdname

    def utcoffset(self, dt):
        return self.stdoffset + self.dst(dt)

    def dst(self, dt):
        if dt is None or dt.tzinfo is None:
            return self.ZERO
        assert dt.tzinfo is self
        start, end = USTimeZone.us_dst_range(dt.year)
        dt = dt.replace(tzinfo=None)
        if start + self.HOUR <= dt < end - self.HOUR:
            return self.HOUR
        if end - self.HOUR <= dt < end:
            return self.ZERO if dt.fold else self.HOUR
        if start <= dt < start + self.HOUR:
            return self.HOUR if dt.fold else self.ZERO
        return self.ZERO

    def fromutc(self, dt):
        assert dt.tzinfo is self
        start, end = USTimeZone.us_dst_range(dt.year)
        start = start.replace(tzinfo=self)
        end = end.replace(tzinfo=self)
        std_time = dt + self.stdoffset
        dst_time = std_time + self.HOUR
        if end <= dst_time < end + self.HOUR:
            return std_time.replace(fold=1)
        if std_time < start or dst_time >= end:
            return std_time
        if start <= std_time < end - self.HOUR:
            return dst_time

    @staticmethod
    def us_dst_range(year):
        start = first_sunday_on_or_after(USTimeZone.DSTSTART.replace(year=year))
        end = first_sunday_on_or_after(USTimeZone.DSTEND.replace(year=year))
        return start, end

    @staticmethod
    def first_sunday_on_or_after(dt):
        days_to_go = 6 - dt.weekday()
        if days_to_go:
            dt += timedelta(days_to_go)
        return dt


class LocalTz:
    def __init__(self, tz):
        self.tz = tz
        self._old = None

    @staticmethod
    def _set(tz):
        if hasattr(mod_time, "tzset"):  # Python
            if tz:
                os.environ["TZ"] = tz
            else:
                del os.environ["TZ"]
            mod_time.tzset()
        else:
            if tz:
                os.putenv("TZ", tz)
            else:
                os.unsetenv("TZ")

    def set(self):
        self._old = os.getenv("TZ")
        LocalTz._set(self.tz)

    def unset(self):
        LocalTz._set(self._old)
        self._old = None

    def __enter__(self):
        self.set()

    def __exit__(self, typ, value, trace):
        self.unset()


tz_acdt = timezone(timedelta(hours=9.5), "ACDT")
tz_est = timezone(-timedelta(hours=5), "EST")
tz1 = timezone(timedelta(hours=-1))
tz2 = Cet()
tz3 = USTimeZone(-5, "Eastern", "EST", "EDT")


class Test1TimeZone(unittest.TestCase):
    def test___init__00(self):
        self.assertEqual(str(tz_acdt), "ACDT")
        self.assertEqual(str(tz_acdt), tz_acdt.tzname(None))

    def test___init__01(self):
        self.assertEqual(str(tz_est), "EST")
        self.assertEqual(str(tz_est), tz_est.tzname(None))

    def test___init__02(self):
        self.assertEqual(str(tz1), "UTC-01:00")
        self.assertEqual(str(tz1), tz1.tzname(None))

    def test___init__03(self):
        self.assertEqual(str(tz2), "CET")
        self.assertEqual(str(tz2), tz2.tzname(None))

    def test___init__04(self):
        offset = timedelta(hours=-24, microseconds=1)
        tz = timezone(offset)
        self.assertIsInstance(tz, timezone)

    def test___init__05(self):
        offset = timedelta(hours=24, microseconds=-1)
        tz = timezone(offset)
        self.assertIsInstance(tz, timezone)

    def test___init__06(self):
        offset = timedelta(hours=-24)
        self.assertRaises(ValueError, timezone, offset)

    def test___init__07(self):
        offset = timedelta(hours=24)
        self.assertRaises(ValueError, timezone, offset)

    def test___repr__00(self):
        self.assertEqual(tz1, eval_mod(repr(tz1)))

    def test___eq__00(self):
        self.assertEqual(timezone(timedelta(hours=1)), timezone(timedelta(hours=1)))

    def test___eq__01(self):
        self.assertNotEqual(timezone(timedelta(hours=1)), timezone(timedelta(hours=2)))

    def test___eq__02(self):
        self.assertEqual(timezone(timedelta(hours=-5)), timezone(timedelta(hours=-5), "EST"))

    def test_utcoffset00(self):
        self.assertEqual(str(tz2.utcoffset(None)), "1:00:00")

    def test_utcoffset01(self):
        self.assertEqual(str(tz2.utcoffset(datetime(2010, 3, 27, 12))), "1:00:00")

    def test_utcoffset02(self):
        self.assertEqual(str(tz2.utcoffset(datetime(2010, 3, 28, 12))), "2:00:00")

    def test_utcoffset03(self):
        self.assertEqual(str(tz2.utcoffset(datetime(2010, 10, 30, 12))), "2:00:00")

    def test_utcoffset04(self):
        self.assertEqual(str(tz2.utcoffset(datetime(2010, 10, 31, 12))), "1:00:00")

    def test_tzname00(self):
        self.assertEqual(tz2.tzname(datetime(2011, 1, 1)), "CET")

    def test_tzname01(self):
        self.assertEqual(tz2.tzname(datetime(2011, 8, 1)), "CEST")

    def test_utc00(self):
        self.assertEqual(timezone.utc.utcoffset(None), td0)

    def test_fromutc00(self):
        utc = EPOCH.replace(tzinfo=tz_acdt)
        self.assertEqual(tz_acdt.fromutc(utc), utc + 9.5 * td1h)

    def test_fromutc01(self):
        utc = EPOCH.replace(tzinfo=tz_est)
        self.assertEqual(tz_est.fromutc(utc), utc + 5 * -td1h)

    def test_fromutc02(self):
        utc = datetime(2010, 3, 28, 0, 59, 59, 999_999, tz2)
        dt = tz2.fromutc(utc)
        self.assertEqual(dt, utc + td1h)
        self.assertFalse(dt.fold)

    def test_fromutc03(self):
        utc = datetime(2010, 3, 28, 1, 0, 0, 0, tz2)
        dt = tz2.fromutc(utc)
        self.assertEqual(dt, utc + 2 * td1h)
        self.assertFalse(dt.fold)

    def test_fromutc04(self):
        utc = datetime(2010, 10, 31, 0, 59, 59, 999_999, tz2)
        dt = tz2.fromutc(utc)
        self.assertEqual(dt, utc + 2 * td1h)
        self.assertFalse(dt.fold)

    def test_fromutc05(self):
        utc = datetime(2010, 10, 31, 1, 0, 0, 0, tz2)
        dt = tz2.fromutc(utc)
        self.assertEqual(dt, utc + td1h)
        self.assertTrue(dt.fold)

    def test_fromutc06(self):
        dt1 = tz2.fromutc(datetime(2010, 10, 31, 0, 0, 0, 0, tz2))
        dt2 = tz2.fromutc(datetime(2010, 10, 31, 1, 0, 0, 0, tz2))
        self.assertEqual(dt1, dt2)
        self.assertNotEqual(dt1.fold, dt2.fold)

    def test_aware_datetime00(self):
        t = datetime(1, 1, 1)
        self.assertEqual(tz1.tzname(t), t.replace(tzinfo=tz1).tzname())

    def test_aware_datetime01(self):
        t = datetime(1, 1, 1)
        self.assertEqual(tz1.utcoffset(t), t.replace(tzinfo=tz1).utcoffset())

    def test_aware_datetime02(self):
        t = datetime(1, 1, 1)
        self.assertEqual(tz1.dst(t), t.replace(tzinfo=tz1).dst())

    def test_offset_boundaries00(self):
        td = timedelta(hours=23, minutes=59, seconds=59, microseconds=999999)
        for i in (1, -1):
            self.assertIsInstance(timezone(i * td), timezone)

    def test_offset_boundaries01(self):
        td = timedelta(hours=24)
        for i in (1, -1):
            with self.assertRaises(ValueError):
                timezone(i * td)


### date #####################################################################

d1 = date(2002, 1, 31)
d1r = "datetime.date(0, 0, 730881)"
d2 = date(1956, 1, 31)
d2d1s = (46 * 365 + len(range(1956, 2002, 4))) * 24 * 60 * 60
d3 = date(2002, 3, 1)
d4 = date(2002, 3, 2)
d5 = date(2002, 1, 31)

hour = timedelta(hours=1)
day = timedelta(days=1)
week = timedelta(weeks=1)
max_days = MAXYEAR * 365 + MAXYEAR // 4 - MAXYEAR // 100 + MAXYEAR // 400


class Test2Date(unittest.TestCase):
    def test___init__00(self):
        self.assertEqual(d1.year, 2002)
        self.assertEqual(d1.month, 1)
        self.assertEqual(d1.day, 31)

    @unittest.skipIf(STDLIB, "not supported by standard datetime")
    def test___init__01(self):
        date(0, 0, 1)

    @unittest.skipIf(STDLIB, "not supported by standard datetime")
    def test___init__02(self):
        date(0, 0, max_days)

    def test___init__03(self):
        datetime(2000, 2, 29)

    def test___init__04(self):
        datetime(2004, 2, 29)

    def test___init__05(self):
        datetime(2400, 2, 29)

    def test___init__06(self):
        self.assertRaises(ValueError, datetime, 2000, 2, 30)

    def test___init__07(self):
        self.assertRaises(ValueError, datetime, 2001, 2, 29)

    def test___init__08(self):
        self.assertRaises(ValueError, datetime, 2100, 2, 29)

    def test___init__09(self):
        self.assertRaises(ValueError, datetime, 1900, 2, 29)

    def test___init__10(self):
        self.assertRaises(ValueError, date, MINYEAR - 1, 1, 1)
        self.assertRaises(ValueError, date, MINYEAR, 0, 1)
        self.assertRaises(ValueError, date, MINYEAR, 1, 0)

    def test___init__11(self):
        self.assertRaises(ValueError, date, MAXYEAR + 1, 12, 31)
        self.assertRaises(ValueError, date, MAXYEAR, 13, 31)
        self.assertRaises(ValueError, date, MAXYEAR, 12, 32)

    def test___init__12(self):
        self.assertRaises(ValueError, date, 1, 2, 29)
        self.assertRaises(ValueError, date, 1, 4, 31)
        self.assertRaises(ValueError, date, 1, 6, 31)
        self.assertRaises(ValueError, date, 1, 9, 31)
        self.assertRaises(ValueError, date, 1, 11, 31)

    def test_fromtimestamp00(self):
        with LocalTz("UTC"):
            d = date.fromtimestamp(1012435200)
            self.assertEqual(d, d1)

    def test_fromtimestamp01(self):
        with LocalTz("UTC"):
            d = date.fromtimestamp(1012435200 + 1)
            self.assertEqual(d, d1)

    def test_fromtimestamp02(self):
        with LocalTz("UTC"):
            d = date.fromtimestamp(1012435200 - 1)
            self.assertEqual(d, d1 - timedelta(days=1))

    def test_fromtimestamp03(self):
        with LocalTz("Europe/Rome"):
            d = date.fromtimestamp(1012435200 - 3601)
            self.assertEqual(d, d1 - timedelta(days=1))

    def test_today00(self):
        tm = mod_time.localtime()[:3]
        dt = date.today()
        dd = (dt.year, dt.month, dt.day)
        self.assertEqual(tm, dd)

    def test_fromordinal00(self):
        self.assertEqual(date.fromordinal(1), date(1, 1, 1))

    def test_fromordinal01(self):
        self.assertEqual(date.fromordinal(max_days), date(MAXYEAR, 12, 31))

    def test_fromisoformat00(self):
        self.assertEqual(datetime.fromisoformat("1975-08-10"), datetime(1975, 8, 10))

    def test_year00(self):
        self.assertEqual(d1.year, 2002)

    def test_year01(self):
        self.assertEqual(d2.year, 1956)

    def test_month00(self):
        self.assertEqual(d1.month, 1)

    def test_month01(self):
        self.assertEqual(d4.month, 3)

    def test_day00(self):
        self.assertEqual(d1.day, 31)

    def test_day01(self):
        self.assertEqual(d4.day, 2)

    def test_toordinal00(self):
        self.assertEqual(date(1, 1, 1).toordinal(), 1)

    def test_toordinal01(self):
        self.assertEqual(date(MAXYEAR, 12, 31).toordinal(), max_days)

    def test_timetuple00(self):
        self.assertEqual(d1.timetuple()[:8], (2002, 1, 31, 0, 0, 0, 3, 31))

    def test_timetuple01(self):
        self.assertEqual(d3.timetuple()[:8], (2002, 3, 1, 0, 0, 0, 4, 60))

    def test_replace00(self):
        self.assertEqual(d1.replace(), d1)

    def test_replace01(self):
        self.assertEqual(d1.replace(year=2001), date(2001, 1, 31))

    def test_replace02(self):
        self.assertEqual(d1.replace(month=5), date(2002, 5, 31))

    def test_replace03(self):
        self.assertEqual(d1.replace(day=16), date(2002, 1, 16))

    def test___add__00(self):
        self.assertEqual(d4 + hour, d4)

    def test___add__01(self):
        self.assertEqual(d4 + day, date(2002, 3, 3))

    def test___add__02(self):
        self.assertEqual(d4 + week, date(2002, 3, 9))

    def test___add__03(self):
        self.assertEqual(d4 + 52 * week, date(2003, 3, 1))

    def test___add__04(self):
        self.assertEqual(d4 + -hour, date(2002, 3, 1))

    def test___add__05(self):
        self.assertEqual(d5 + -day, date(2002, 1, 30))

    def test___add__06(self):
        self.assertEqual(d4 + -week, date(2002, 2, 23))

    def test___sub__00(self):
        d = d1 - d2
        self.assertEqual(d.total_seconds(), d2d1s)

    def test___sub__01(self):
        self.assertEqual(d4 - hour, d4)

    def test___sub__02(self):
        self.assertEqual(d4 - day, date(2002, 3, 1))

    def test___sub__03(self):
        self.assertEqual(d4 - week, date(2002, 2, 23))

    def test___sub__04(self):
        self.assertEqual(d4 - 52 * week, date(2001, 3, 3))

    def test___sub__05(self):
        self.assertEqual(d4 - -hour, date(2002, 3, 3))

    def test___sub__06(self):
        self.assertEqual(d4 - -day, date(2002, 3, 3))

    def test___sub__07(self):
        self.assertEqual(d4 - -week, date(2002, 3, 9))

    def test___eq__00(self):
        self.assertEqual(d1, d5)

    def test___eq__01(self):
        self.assertFalse(d1 != d5)

    def test___eq__02(self):
        self.assertTrue(d2 != d5)

    def test___eq__03(self):
        self.assertTrue(d5 != d2)

    def test___eq__04(self):
        self.assertFalse(d2 == d5)

    def test___eq__05(self):
        self.assertFalse(d5 == d2)

    def test___eq__06(self):
        self.assertFalse(d1 == None)

    def test___eq__07(self):
        self.assertTrue(d1 != None)

    def test___le__00(self):
        self.assertTrue(d1 <= d5)

    def test___le__01(self):
        self.assertTrue(d2 <= d5)

    def test___le__02(self):
        self.assertFalse(d5 <= d2)

    def test___ge__00(self):
        self.assertTrue(d1 >= d5)

    def test___ge__01(self):
        self.assertTrue(d5 >= d2)

    def test___ge__02(self):
        self.assertFalse(d2 >= d5)

    def test___lt__00(self):
        self.assertFalse(d1 < d5)

    def test___lt__01(self):
        self.assertTrue(d2 < d5)

    def test___lt__02(self):
        self.assertFalse(d5 < d2)

    def test___gt__00(self):
        self.assertFalse(d1 > d5)

    def test___gt__01(self):
        self.assertTrue(d5 > d2)

    def test___gt__02(self):
        self.assertFalse(d2 > d5)

    def test_weekday00(self):
        for i in range(7):
            # March 4, 2002 is a Monday
            self.assertEqual(datetime(2002, 3, 4 + i).weekday(), i)
            # January 2, 1956 is a Monday
            self.assertEqual(datetime(1956, 1, 2 + i).weekday(), i)

    def test_isoweekday00(self):
        for i in range(7):
            self.assertEqual(datetime(2002, 3, 4 + i).isoweekday(), i + 1)
            self.assertEqual(datetime(1956, 1, 2 + i).isoweekday(), i + 1)

    def test_isoformat00(self):
        self.assertEqual(d1.isoformat(), "2002-01-31")

    @unittest.skipIf(STDLIB, "standard datetime differs")
    def test___repr__00(self):
        self.assertEqual(repr(d1), d1r)

    def test___repr__01(self):
        self.assertEqual(d1, eval_mod(repr(d1)))

    def test___hash__00(self):
        self.assertEqual(d1, d5)
        self.assertEqual(hash(d1), hash(d5))

    def test___hash__01(self):
        dd1 = d1 + timedelta(weeks=7)
        dd5 = d5 + timedelta(days=7 * 7)
        self.assertEqual(hash(dd1), hash(dd5))

    def test___hash__02(self):
        d = {d1: 1}
        d[d5] = 2
        self.assertEqual(len(d), 1)
        self.assertEqual(d[d1], 2)


### time #####################################################################

t1 = time(18, 45, 3, 1234)
t1r = "datetime.time(microsecond=67503001234, tzinfo=None, fold=0)"
t1f = time(18, 45, 3, 1234, fold=1)
t1fr = f"datetime.time(microsecond=67503001234, tzinfo=None, fold=1)"
t1z = time(18, 45, 3, 1234, tz1)
t1zr = f"datetime.time(microsecond=67503001234, tzinfo={repr(tz1)}, fold=0)"
t2 = time(12, 59, 59, 100)
t2z = time(12, 59, 59, 100, tz2)
t3 = time(18, 45, 3, 1234)
t3z = time(18, 45, 3, 1234, tz2)
t4 = time(18, 45, 3, 1234, fold=1)
t4z = time(18, 45, 3, 1234, tz2, fold=1)
t5z = time(20, 45, 3, 1234, tz2)


class Test3Time(unittest.TestCase):
    def test___init__00(self):
        t = time()
        self.assertEqual(t.hour, 0)
        self.assertEqual(t.minute, 0)
        self.assertEqual(t.second, 0)
        self.assertEqual(t.microsecond, 0)
        self.assertEqual(t.tzinfo, None)
        self.assertEqual(t.fold, 0)

    def test___init__01(self):
        t = time(12)
        self.assertEqual(t.hour, 12)
        self.assertEqual(t.minute, 0)
        self.assertEqual(t.second, 0)
        self.assertEqual(t.microsecond, 0)
        self.assertEqual(t.tzinfo, None)
        self.assertEqual(t.fold, 0)

    def test___init__02(self):
        self.assertEqual(t1z.hour, 18)
        self.assertEqual(t1z.minute, 45)
        self.assertEqual(t1z.second, 3)
        self.assertEqual(t1z.microsecond, 1234)
        self.assertEqual(t1z.tzinfo, tz1)
        self.assertEqual(t1z.fold, 0)

    def test___init__03(self):
        t = time(microsecond=1, fold=1)
        self.assertEqual(t.fold, 1)

    @unittest.skipIf(STDLIB, "not supported by standard datetime")
    def test___init__04(self):
        time(microsecond=24 * 60 * 60 * 1_000_000 - 1)

    def test___init__05(self):
        self.assertRaises(ValueError, time, -1, 0, 0, 0)
        self.assertRaises(ValueError, time, 0, -1, 0, 0)
        self.assertRaises(ValueError, time, 0, 0, -1, 0)
        self.assertRaises(ValueError, time, 0, 0, 0, -1)
        self.assertRaises(ValueError, time, 0, 0, 0, 0, fold=-1)

    def test___init__06(self):
        self.assertRaises(ValueError, time, 24, 0, 0, 0)
        self.assertRaises(ValueError, time, 0, 60, 0, 0)
        self.assertRaises(ValueError, time, 0, 0, 60, 0)
        self.assertRaises(ValueError, time, 0, 0, 0, 0, fold=2)

    @unittest.skipIf(STDLIB, "not supported by standard datetime")
    def test___init__07(self):
        self.assertRaises(ValueError, time, microsecond=24 * 60 * 60 * 1_000_000)

    def test_fromisoformat00(self):
        self.assertEqual(time.fromisoformat("01"), time(1))

    def test_fromisoformat01(self):
        self.assertEqual(time.fromisoformat("13:30"), time(13, 30))

    def test_fromisoformat02(self):
        self.assertEqual(time.fromisoformat("23:30:12"), time(23, 30, 12))

    def test_fromisoformat03(self):
        self.assertEqual(str(time.fromisoformat("11:03:04+01:00")), "11:03:04+01:00")

    def test_hour00(self):
        self.assertEqual(t1.hour, 18)

    def test_hour01(self):
        self.assertEqual(t2z.hour, 12)

    def test_minute00(self):
        self.assertEqual(t1.minute, 45)

    def test_minute01(self):
        self.assertEqual(t2z.minute, 59)

    def test_second00(self):
        self.assertEqual(t1.second, 3)

    def test_second01(self):
        self.assertEqual(t2z.second, 59)

    def test_microsecond00(self):
        self.assertEqual(t1.microsecond, 1234)

    def test_microsecond01(self):
        self.assertEqual(t2z.microsecond, 100)

    def test_tzinfo00(self):
        self.assertEqual(t1.tzinfo, None)

    def test_tzinfo01(self):
        self.assertEqual(t2z.tzinfo, tz2)

    def test_fold00(self):
        self.assertEqual(t1.fold, 0)

    def test_replace00(self):
        self.assertEqual(t2z.replace(), t2z)

    def test_replace01(self):
        self.assertEqual(t2z.replace(hour=20), time(20, 59, 59, 100, tz2))

    def test_replace02(self):
        self.assertEqual(t2z.replace(minute=4), time(12, 4, 59, 100, tz2))

    def test_replace03(self):
        self.assertEqual(t2z.replace(second=16), time(12, 59, 16, 100, tz2))

    def test_replace04(self):
        self.assertEqual(t2z.replace(microsecond=99), time(12, 59, 59, 99, tz2))

    def test_replace05(self):
        self.assertEqual(t2z.replace(tzinfo=tz1), time(12, 59, 59, 100, tz1))

    def test_isoformat00(self):
        self.assertEqual(t1.isoformat(), "18:45:03.001234")

    def test_isoformat01(self):
        self.assertEqual(t1z.isoformat(), "18:45:03.001234-01:00")

    def test_isoformat02(self):
        self.assertEqual(t2z.isoformat(), "12:59:59.000100+01:00")

    @unittest.skipIf(STDLIB, "standard datetime differs")
    def test___repr__00(self):
        self.assertEqual(repr(t1), t1r)

    @unittest.skipIf(STDLIB, "standard datetime differs")
    def test___repr__01(self):
        self.assertEqual(repr(t1f), t1fr)

    @unittest.skipIf(STDLIB, "standard datetime differs")
    def test___repr__02(self):
        self.assertEqual(repr(t1z), t1zr)

    def test___repr__03(self):
        self.assertEqual(t1, eval_mod(repr(t1)))

    def test___repr__04(self):
        self.assertEqual(t1z, eval_mod(repr(t1z)))

    def test___repr__05(self):
        self.assertEqual(t4, eval_mod(repr(t4)))

    def test___repr__06(self):
        dt = eval_mod(repr(t4z))
        self.assertEqual(t4z, eval_mod(repr(t4z)))

    def test___bool__00(self):
        self.assertTrue(t1)

    def test___bool__01(self):
        self.assertTrue(t1z)

    def test___bool__02(self):
        self.assertTrue(time())

    def test___eq__00(self):
        self.assertEqual(t1, t1)

    def test___eq__01(self):
        self.assertEqual(t1z, t1z)

    def test___eq__02(self):
        self.assertNotEqual(t1, t1z)

    def test___eq__03(self):
        self.assertNotEqual(t1z, t2z)

    def test___eq__04(self):
        self.assertEqual(t1z, t5z)

    def test___eq__05(self):
        self.assertEqual(t1, t1f)

    def test___lt__00(self):
        self.assertTrue(t2 < t1)

    def test___lt__01(self):
        self.assertTrue(t2z < t1z)

    def test___lt__02(self):
        self.assertRaises(TypeError, t1.__lt__, t1z)

    def test___le__00(self):
        self.assertTrue(t3 <= t1)

    def test___le__01(self):
        self.assertTrue(t1z <= t5z)

    def test___le__02(self):
        self.assertRaises(TypeError, t1.__le__, t1z)

    def test___ge__00(self):
        self.assertTrue(t1 >= t3)

    def test___ge__01(self):
        self.assertTrue(t5z >= t1z)

    def test___ge__02(self):
        self.assertRaises(TypeError, t1.__ge__, t1z)

    def test___gt__00(self):
        self.assertTrue(t1 > t2)

    def test___gt__01(self):
        self.assertTrue(t1z > t2z)

    def test___gt__02(self):
        self.assertRaises(TypeError, t1.__gt__, t1z)

    def test___hash__00(self):
        self.assertEqual(t1, t3)
        self.assertEqual(hash(t1), hash(t3))

    def test___hash__01(self):
        d = {t1: 1}
        d[t3] = 3
        self.assertEqual(len(d), 1)
        self.assertEqual(d[t1], 3)

    def test___hash__02(self):
        self.assertNotEqual(t1, t1z)
        self.assertNotEqual(hash(t1), hash(t1z))

    def test___hash__03(self):
        self.assertNotEqual(t1z, t3z)
        self.assertNotEqual(hash(t1z), hash(t3z))

    def test___hash__04(self):
        tf = t1.replace(fold=1)
        self.assertEqual(t1, tf)
        self.assertEqual(hash(t1), hash(tf))

    def test_utcoffset00(self):
        self.assertEqual(t1.utcoffset(), None)

    def test_utcoffset01(self):
        self.assertEqual(t1z.utcoffset(), timedelta(hours=-1))

    def test_utcoffset02(self):
        self.assertEqual(t2z.utcoffset(), timedelta(hours=1))

    def test_dst00(self):
        self.assertEqual(t1.dst(), None)

    def test_dst01(self):
        self.assertEqual(t1z.dst(), None)

    def test_dst02(self):
        self.assertEqual(t2z.dst(), td0)

    def test_tzname00(self):
        self.assertEqual(t1.tzname(), None)

    def test_tzname01(self):
        self.assertEqual(t1z.tzname(), "UTC-01:00")

    def test_tzname02(self):
        self.assertEqual(t2z.tzname(), "CET")

    def test_constant00(self):
        self.assertIsInstance(timedelta.resolution, timedelta)
        self.assertTrue(timedelta.max > timedelta.min)

    def test_constant01(self):
        self.assertEqual(time.min, time(0))

    def test_constant02(self):
        self.assertEqual(time.max, time(23, 59, 59, 999_999))

    def test_constant03(self):
        self.assertEqual(time.resolution, timedelta(microseconds=1))


### datetime #################################################################

dt1 = datetime(2002, 1, 31)
dt1z1 = datetime(2002, 1, 31, tzinfo=tz1)
dt1z2 = datetime(2002, 1, 31, tzinfo=tz2)
dt2 = datetime(1956, 1, 31)
dt3 = datetime(2002, 3, 1, 12, 59, 59, 100, tz2)
dt4 = datetime(2002, 3, 2, 17, 6)
dt5 = datetime(2002, 1, 31)
dt5z2 = datetime(2002, 1, 31, tzinfo=tz2)

dt1r = "datetime.datetime(2002, 1, 31, 0, 0, 0, 0, None, fold=0)"
dt3r = "datetime.datetime(2002, 3, 1, 12, 59, 59, 100, Cet(), fold=0)"
dt4r = "datetime.datetime(2002, 3, 2, 17, 6, 0, 0, None, fold=0)"

d1t1 = datetime(2002, 1, 31, 18, 45, 3, 1234)
d1t1f = datetime(2002, 1, 31, 18, 45, 3, 1234, fold=1)
d1t1z = datetime(2002, 1, 31, 18, 45, 3, 1234, tz1)

dt27tz2 = datetime(2010, 3, 27, 12, tzinfo=tz2)  # last CET day
dt28tz2 = datetime(2010, 3, 28, 12, tzinfo=tz2)  # first CEST day
dt30tz2 = datetime(2010, 10, 30, 12, tzinfo=tz2)  # last CEST day
dt31tz2 = datetime(2010, 10, 31, 12, tzinfo=tz2)  # first CET day


# Tests where datetime depens on date and time
class Test4DateTime(unittest.TestCase):
    def test_combine00(self):
        dt = datetime.combine(d1, t1)
        self.assertEqual(dt, d1t1)

    def test_combine01(self):
        dt = datetime.combine(d1, t1)
        self.assertEqual(dt.date(), d1)

    def test_combine02(self):
        dt1 = datetime.combine(d1, t1)
        dt2 = datetime.combine(dt1, t1)
        self.assertEqual(dt1, dt2)

    def test_combine03(self):
        dt = datetime.combine(d1, t1)
        self.assertEqual(dt.time(), t1)

    def test_combine04(self):
        dt = datetime.combine(d1, t1, tz1)
        self.assertEqual(dt, d1t1z)

    def test_combine05(self):
        dt = datetime.combine(d1, t1z)
        self.assertEqual(dt, d1t1z)

    def test_combine06(self):
        dt = datetime.combine(d1, t1f)
        self.assertEqual(dt, d1t1f)

    def test_date00(self):
        self.assertEqual(d1t1.date(), d1)

    def test_time00(self):
        self.assertEqual(d1t1.time(), t1)

    def test_time01(self):
        self.assertNotEqual(d1t1z.time(), t1z)

    def test_timetz00(self):
        self.assertEqual(d1t1.timetz(), t1)

    def test_timetz01(self):
        self.assertEqual(d1t1z.timetz(), t1z)

    def test_timetz02(self):
        self.assertEqual(d1t1f.timetz(), t1f)


# Tests where datetime is independent from date and time
class Test5DateTime(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for k in ("date", "time"):
            del mod_datetime.__dict__[k]

    def test___init__00(self):
        d = datetime(2002, 3, 1, 12, 0, fold=1)
        self.assertEqual(d.year, 2002)
        self.assertEqual(d.month, 3)
        self.assertEqual(d.day, 1)
        self.assertEqual(d.hour, 12)
        self.assertEqual(d.minute, 0)
        self.assertEqual(d.second, 0)
        self.assertEqual(d.microsecond, 0)
        self.assertEqual(d.tzinfo, None)
        self.assertEqual(d.fold, 1)

    def test___init__01(self):
        self.assertEqual(dt3.year, 2002)
        self.assertEqual(dt3.month, 3)
        self.assertEqual(dt3.day, 1)
        self.assertEqual(dt3.hour, 12)
        self.assertEqual(dt3.minute, 59)
        self.assertEqual(dt3.second, 59)
        self.assertEqual(dt3.microsecond, 100)
        self.assertEqual(dt3.tzinfo, tz2)
        self.assertEqual(dt3.fold, 0)

    def test___init__02(self):
        datetime(MINYEAR, 1, 1)

    def test___init__03(self):
        datetime(MAXYEAR, 12, 31)

    def test___init__04(self):
        self.assertRaises(ValueError, datetime, MINYEAR - 1, 1, 1)

    def test___init__05(self):
        self.assertRaises(ValueError, datetime, MAXYEAR + 1, 1, 1)

    def test___init__06(self):
        self.assertRaises(ValueError, datetime, 2000, 0, 1)

    def test___init__07(self):
        datetime(2000, 2, 29)

    def test___init__08(self):
        datetime(2004, 2, 29)

    def test___init__09(self):
        datetime(2400, 2, 29)

    def test___init__10(self):
        self.assertRaises(ValueError, datetime, 2000, 2, 30)

    def test___init__11(self):
        self.assertRaises(ValueError, datetime, 2001, 2, 29)

    def test___init__12(self):
        self.assertRaises(ValueError, datetime, 2100, 2, 29)

    def test___init__13(self):
        self.assertRaises(ValueError, datetime, 1900, 2, 29)

    def test___init__14(self):
        self.assertRaises(ValueError, datetime, 2000, 1, 0)

    def test___init__15(self):
        self.assertRaises(ValueError, datetime, 2000, 1, 32)

    def test___init__16(self):
        self.assertRaises(ValueError, datetime, 2000, 1, 31, -1)

    def test___init__17(self):
        self.assertRaises(ValueError, datetime, 2000, 1, 31, 24)

    def test___init__18(self):
        self.assertRaises(ValueError, datetime, 2000, 1, 31, 23, -1)

    def test___init__19(self):
        self.assertRaises(ValueError, datetime, 2000, 1, 31, 23, 60)

    def test___init__20(self):
        self.assertRaises(ValueError, datetime, 2000, 1, 31, 23, 59, -1)

    def test___init__21(self):
        self.assertRaises(ValueError, datetime, 2000, 1, 31, 23, 59, 60)

    def test___init__22(self):
        self.assertEqual(dt1, eval_mod(dt1r))

    def test___init__23(self):
        self.assertEqual(dt3, eval_mod(dt3r))

    def test___init__24(self):
        self.assertEqual(dt4, eval_mod(dt4r))

    def test_fromtimestamp00(self):
        with LocalTz("Europe/Rome"):
            ts = 1012499103.001234
            if LOCALTZ:
                dt = datetime.fromtimestamp(ts)
                self.assertEqual(dt, d1t1)
            else:
                self.assertRaises(NotImplementedError, datetime.fromtimestamp, ts)

    def test_fromtimestamp01(self):
        ts = 1012506303.001234
        self.assertEqual(datetime.fromtimestamp(ts, tz1), d1t1z)

    def test_fromtimestamp02(self):
        ts = 1269687600
        self.assertEqual(datetime.fromtimestamp(ts, tz2), dt27tz2)

    def test_fromtimestamp03(self):
        ts = 1269770400
        self.assertEqual(datetime.fromtimestamp(ts, tz2), dt28tz2)

    def test_fromtimestamp04(self):
        with LocalTz("Europe/Rome"):
            dt = datetime(2010, 10, 31, 0, 30, tzinfo=timezone.utc)
            ts = (dt - EPOCH).total_seconds()
            dt = dt.replace(tzinfo=None) + 2 * td1h
            if LOCALTZ:
                ds = datetime.fromtimestamp(ts)
                self.assertEqual(ds, dt)
                self.assertFalse(ds.fold)
            else:
                self.assertRaises(NotImplementedError, datetime.fromtimestamp, ts)

    def test_fromtimestamp05(self):
        with LocalTz("Europe/Rome"):
            dt = datetime(2010, 10, 31, 1, 30, tzinfo=timezone.utc)
            ts = (dt - EPOCH).total_seconds()
            dt = dt.replace(tzinfo=None) + 1 * td1h
            if LOCALTZ:
                ds = datetime.fromtimestamp(ts)
                self.assertEqual(ds, dt)
                self.assertTrue(ds.fold)
            else:
                self.assertRaises(NotImplementedError, datetime.fromtimestamp, ts)

    def test_fromtimestamp06(self):
        with LocalTz("US/Eastern"):
            dt = datetime(2020, 11, 1, 5, 30, tzinfo=timezone.utc)
            ts = (dt - EPOCH).total_seconds()
            dt = dt.replace(tzinfo=None) - 4 * td1h
            if LOCALTZ:
                ds = datetime.fromtimestamp(ts)
                self.assertEqual(ds, dt)
            else:
                self.assertRaises(NotImplementedError, datetime.fromtimestamp, ts)

    def test_fromtimestamp07(self):
        with LocalTz("US/Eastern"):
            dt = datetime(2020, 11, 1, 7, 30, tzinfo=timezone.utc)
            ts = (dt - EPOCH).total_seconds()
            dt = dt.replace(tzinfo=None) - 5 * td1h
            if LOCALTZ:
                ds = datetime.fromtimestamp(ts)
                self.assertEqual(ds, dt)
            else:
                self.assertRaises(NotImplementedError, datetime.fromtimestamp, ts)

    @unittest.skipIf(not LOCALTZ, "naive datetime not supported")
    def test_now00(self):
        tm = datetime(*mod_time.localtime()[:6])
        dt = datetime.now()
        self.assertAlmostEqual(tm, dt, delta=timedelta(seconds=1))

    def test_now01(self):
        tm = datetime(*mod_time.gmtime()[:6], tzinfo=tz2)
        tm += tz2.utcoffset(tm)
        dt = datetime.now(tz2)
        self.assertAlmostEqual(tm, dt, delta=timedelta(seconds=1))

    def test_fromordinal00(self):
        self.assertEqual(datetime.fromordinal(1), datetime(1, 1, 1))

    def test_fromordinal01(self):
        self.assertEqual(datetime.fromordinal(max_days), datetime(MAXYEAR, 12, 31))

    def test_fromisoformat00(self):
        self.assertEqual(datetime.fromisoformat("1975-08-10"), datetime(1975, 8, 10))

    def test_fromisoformat01(self):
        self.assertEqual(datetime.fromisoformat("1975-08-10 23"), datetime(1975, 8, 10, 23))

    def test_fromisoformat02(self):
        self.assertEqual(datetime.fromisoformat("1975-08-10 23:30"), datetime(1975, 8, 10, 23, 30))

    def test_fromisoformat03(self):
        self.assertEqual(
            datetime.fromisoformat("1975-08-10 23:30:12"), datetime(1975, 8, 10, 23, 30, 12)
        )

    def test_fromisoformat04(self):
        self.assertEqual(
            str(datetime.fromisoformat("1975-08-10 23:30:12+01:00")), "1975-08-10 23:30:12+01:00"
        )

    def test_year00(self):
        self.assertEqual(dt1.year, 2002)

    def test_year01(self):
        self.assertEqual(dt2.year, 1956)

    def test_month00(self):
        self.assertEqual(dt1.month, 1)

    def test_month01(self):
        self.assertEqual(dt3.month, 3)

    def test_day00(self):
        self.assertEqual(dt1.day, 31)

    def test_day01(self):
        self.assertEqual(dt4.day, 2)

    def test_hour00(self):
        self.assertEqual(dt1.hour, 0)

    def test_hour01(self):
        self.assertEqual(dt3.hour, 12)

    def test_minute00(self):
        self.assertEqual(dt1.minute, 0)

    def test_minute01(self):
        self.assertEqual(dt3.minute, 59)

    def test_second00(self):
        self.assertEqual(dt1.second, 0)

    def test_second01(self):
        self.assertEqual(dt3.second, 59)

    def test_microsecond00(self):
        self.assertEqual(dt1.microsecond, 0)

    def test_microsecond01(self):
        self.assertEqual(dt3.microsecond, 100)

    def test_tzinfo00(self):
        self.assertEqual(dt1.tzinfo, None)

    def test_tzinfo01(self):
        self.assertEqual(dt3.tzinfo, tz2)

    def test_fold00(self):
        self.assertEqual(dt1.fold, 0)

    def test___add__00(self):
        self.assertEqual(dt4 + hour, datetime(2002, 3, 2, 18, 6))

    def test___add__01(self):
        self.assertEqual(hour + dt4, datetime(2002, 3, 2, 18, 6))

    def test___add__02(self):
        self.assertEqual(dt4 + 10 * hour, datetime(2002, 3, 3, 3, 6))

    def test___add__03(self):
        self.assertEqual(dt4 + day, datetime(2002, 3, 3, 17, 6))

    def test___add__04(self):
        self.assertEqual(dt4 + week, datetime(2002, 3, 9, 17, 6))

    def test___add__05(self):
        self.assertEqual(dt4 + 52 * week, datetime(2003, 3, 1, 17, 6))

    def test___add__06(self):
        self.assertEqual(dt4 + (week + day + hour), datetime(2002, 3, 10, 18, 6))

    def test___add__07(self):
        self.assertEqual(dt5 + -day, datetime(2002, 1, 30))

    def test___add__08(self):
        self.assertEqual(-hour + dt4, datetime(2002, 3, 2, 16, 6))

    def test___sub__00(self):
        d = dt1 - dt2
        self.assertEqual(d.total_seconds(), d2d1s)

    def test___sub__01(self):
        self.assertEqual(dt4 - hour, datetime(2002, 3, 2, 16, 6))

    def test___sub__02(self):
        self.assertEqual(dt4 - hour, dt4 + -hour)

    def test___sub__03(self):
        self.assertEqual(dt4 - 20 * hour, datetime(2002, 3, 1, 21, 6))

    def test___sub__04(self):
        self.assertEqual(dt4 - day, datetime(2002, 3, 1, 17, 6))

    def test___sub__05(self):
        self.assertEqual(dt4 - week, datetime(2002, 2, 23, 17, 6))

    def test___sub__06(self):
        self.assertEqual(dt4 - 52 * week, datetime(2001, 3, 3, 17, 6))

    def test___sub__07(self):
        self.assertEqual(dt4 - (week + day + hour), datetime(2002, 2, 22, 16, 6))

    def test_computation00(self):
        self.assertEqual((dt4 + week) - dt4, week)

    def test_computation01(self):
        self.assertEqual((dt4 + day) - dt4, day)

    def test_computation02(self):
        self.assertEqual((dt4 + hour) - dt4, hour)

    def test_computation03(self):
        self.assertEqual(dt4 - (dt4 + week), -week)

    def test_computation04(self):
        self.assertEqual(dt4 - (dt4 + day), -day)

    def test_computation05(self):
        self.assertEqual(dt4 - (dt4 + hour), -hour)

    def test_computation06(self):
        self.assertEqual(dt4 - (dt4 - week), week)

    def test_computation07(self):
        self.assertEqual(dt4 - (dt4 - day), day)

    def test_computation08(self):
        self.assertEqual(dt4 - (dt4 - hour), hour)

    def test_computation09(self):
        self.assertEqual(dt4 + (week + day + hour), (((dt4 + week) + day) + hour))

    def test_computation10(self):
        self.assertEqual(dt4 - (week + day + hour), (((dt4 - week) - day) - hour))

    def test___eq__00(self):
        self.assertEqual(dt1, dt5)

    def test___eq__01(self):
        self.assertFalse(dt1 != dt5)

    def test___eq__02(self):
        self.assertTrue(dt2 != dt5)

    def test___eq__03(self):
        self.assertTrue(dt5 != dt2)

    def test___eq__04(self):
        self.assertFalse(dt2 == dt5)

    def test___eq__05(self):
        self.assertFalse(dt5 == dt2)

    def test___eq__06(self):
        self.assertFalse(dt1 == dt1z1)

    def test___eq__07(self):
        self.assertFalse(dt1z1 == dt1z2)

    def test___eq__08(self):
        self.assertTrue(dt1z2 == dt5z2)

    def test___le__00(self):
        self.assertTrue(dt1 <= dt5)

    def test___le__01(self):
        self.assertTrue(dt2 <= dt5)

    def test___le__02(self):
        self.assertFalse(dt5 <= dt2)

    def test___le__03(self):
        self.assertFalse(dt1z1 <= dt1z2)

    def test___le__04(self):
        self.assertTrue(dt1z2 <= dt5z2)

    def test___le__05(self):
        self.assertRaises(TypeError, dt1.__le__, dt1z1)

    def test___ge__00(self):
        self.assertTrue(dt1 >= dt5)

    def test___ge__01(self):
        self.assertTrue(dt5 >= dt2)

    def test___ge__02(self):
        self.assertFalse(dt2 >= dt5)

    def test___ge__03(self):
        self.assertTrue(dt1z1 >= dt1z2)

    def test___ge__04(self):
        self.assertTrue(dt1z2 >= dt5z2)

    def test___ge__05(self):
        self.assertRaises(TypeError, dt1.__ge__, dt1z1)

    def test___lt__00(self):
        self.assertFalse(dt1 < dt5)

    def test___lt__01(self):
        self.assertTrue(dt2 < dt5)

    def test___lt__02(self):
        self.assertFalse(dt5 < dt2)

    def test___lt__03(self):
        self.assertFalse(dt1z1 < dt1z2)

    def test___lt__04(self):
        self.assertFalse(dt1z2 < dt5z2)

    def test___lt__05(self):
        self.assertRaises(TypeError, dt1.__lt__, dt1z1)

    def test___gt__00(self):
        self.assertFalse(dt1 > dt5)

    def test___gt__01(self):
        self.assertTrue(dt5 > dt2)

    def test___gt__02(self):
        self.assertFalse(dt2 > dt5)

    def test___gt__03(self):
        self.assertTrue(dt1z1 > dt1z2)

    def test___gt__04(self):
        self.assertFalse(dt1z2 > dt5z2)

    def test___gt__05(self):
        self.assertRaises(TypeError, dt1.__gt__, dt1z1)

    def test_replace00(self):
        self.assertEqual(dt3.replace(), dt3)

    def test_replace01(self):
        self.assertEqual(dt3.replace(year=2001), datetime(2001, 3, 1, 12, 59, 59, 100, tz2))

    def test_replace02(self):
        self.assertEqual(dt3.replace(month=4), datetime(2002, 4, 1, 12, 59, 59, 100, tz2))

    def test_replace03(self):
        self.assertEqual(dt3.replace(day=16), datetime(2002, 3, 16, 12, 59, 59, 100, tz2))

    def test_replace04(self):
        self.assertEqual(dt3.replace(hour=13), datetime(2002, 3, 1, 13, 59, 59, 100, tz2))

    def test_replace05(self):
        self.assertEqual(dt3.replace(minute=0), datetime(2002, 3, 1, 12, 0, 59, 100, tz2))

    def test_replace06(self):
        self.assertEqual(dt3.replace(second=1), datetime(2002, 3, 1, 12, 59, 1, 100, tz2))

    def test_replace07(self):
        self.assertEqual(dt3.replace(microsecond=99), datetime(2002, 3, 1, 12, 59, 59, 99, tz2))

    def test_replace08(self):
        self.assertEqual(dt3.replace(tzinfo=tz1), datetime(2002, 3, 1, 12, 59, 59, 100, tz1))

    def test_replace09(self):
        self.assertRaises(ValueError, datetime(2000, 2, 29).replace, year=2001)

    def test_astimezone00(self):
        dt = datetime(2002, 3, 1, 11, 59, 59, 100, timezone.utc)
        self.assertEqual(dt3.astimezone(timezone.utc), dt)

    def test_astimezone01(self):
        self.assertIs(dt1z1.astimezone(tz1), dt1z1)

    def test_astimezone02(self):
        dt = datetime(2002, 1, 31, 2, 0, tzinfo=tz2)
        self.assertEqual(dt1z1.astimezone(tz2), dt)

    def test_astimezone03(self):
        dt = datetime(2002, 1, 31, 10, 30, tzinfo=tz_acdt)
        self.assertEqual(dt1z1.astimezone(tz_acdt), dt)

    def test_astimezone04(self):
        with LocalTz("Europe/Rome"):
            dt1 = dt27tz2
            dt2 = dt1.replace(tzinfo=None)
            if LOCALTZ:
                self.assertEqual(dt1, dt2.astimezone(tz2))
            else:
                self.assertRaises(NotImplementedError, dt2.astimezone, tz2)

    def test_astimezone05(self):
        with LocalTz("Europe/Rome"):
            dt1 = dt28tz2
            dt2 = dt1.replace(tzinfo=None)
            if LOCALTZ:
                self.assertEqual(dt1, dt2.astimezone(tz2))
            else:
                self.assertRaises(NotImplementedError, dt2.astimezone, tz2)

    def test_astimezone06(self):
        with LocalTz("Europe/Rome"):
            dt1 = dt30tz2
            dt2 = dt1.replace(tzinfo=None)
            if LOCALTZ:
                self.assertEqual(dt1, dt2.astimezone(tz2))
            else:
                self.assertRaises(NotImplementedError, dt2.astimezone, tz2)

    def test_astimezone07(self):
        with LocalTz("Europe/Rome"):
            dt1 = dt31tz2
            dt2 = dt1.replace(tzinfo=None)
            if LOCALTZ:
                self.assertEqual(dt1, dt2.astimezone(tz2))
            else:
                self.assertRaises(NotImplementedError, dt2.astimezone, tz2)

    def test_astimezone08(self):
        with LocalTz("Europe/Rome"):
            dt1 = dt3
            dt2 = dt1.replace(tzinfo=None)
            if LOCALTZ:
                self.assertEqual(dt1, dt2.astimezone(tz2))
            else:
                self.assertRaises(NotImplementedError, dt2.astimezone, tz2)

    def test_utcoffset00(self):
        self.assertEqual(dt1.utcoffset(), None)

    def test_utcoffset01(self):
        self.assertEqual(dt27tz2.utcoffset(), timedelta(hours=1))

    def test_utcoffset02(self):
        self.assertEqual(dt28tz2.utcoffset(), timedelta(hours=2))

    def test_utcoffset03(self):
        self.assertEqual(dt30tz2.utcoffset(), timedelta(hours=2))

    def test_utcoffset04(self):
        self.assertEqual(dt31tz2.utcoffset(), timedelta(hours=1))

    def test_dst00(self):
        self.assertEqual(dt1.dst(), None)

    def test_dst01(self):
        self.assertEqual(dt27tz2.dst(), timedelta(hours=0))

    def test_dst02(self):
        self.assertEqual(dt28tz2.dst(), timedelta(hours=1))

    def test_tzname00(self):
        self.assertEqual(dt1.tzname(), None)

    def test_tzname01(self):
        self.assertEqual(dt27tz2.tzname(), "CET")

    def test_tzname02(self):
        self.assertEqual(dt28tz2.tzname(), "CEST")

    def test_timetuple00(self):
        with LocalTz("Europe/Rome"):
            self.assertEqual(dt1.timetuple()[:8], (2002, 1, 31, 0, 0, 0, 3, 31))

    @unittest.skip("broken when running with non-UTC timezone")
    def test_timetuple01(self):
        self.assertEqual(dt27tz2.timetuple()[:8], (2010, 3, 27, 12, 0, 0, 5, 86))

    @unittest.skip("broken when running with non-UTC timezone")
    def test_timetuple02(self):
        self.assertEqual(dt28tz2.timetuple()[:8], (2010, 3, 28, 12, 0, 0, 6, 87))

    def test_timetuple03(self):
        with LocalTz("Europe/Rome"):
            self.assertEqual(
                dt27tz2.replace(tzinfo=None).timetuple()[:8], (2010, 3, 27, 12, 0, 0, 5, 86)
            )

    def test_timetuple04(self):
        self.assertEqual(
            dt28tz2.replace(tzinfo=None).timetuple()[:8], (2010, 3, 28, 12, 0, 0, 6, 87)
        )

    def test_toordinal00(self):
        self.assertEqual(datetime(1, 1, 1).toordinal(), 1)

    def test_toordinal01(self):
        self.assertEqual(datetime(1, 12, 31).toordinal(), 365)

    def test_toordinal02(self):
        self.assertEqual(datetime(2, 1, 1).toordinal(), 366)

    def test_toordinal03(self):
        # https://www.timeanddate.com/date/dateadded.html?d1=1&m1=1&y1=1&type=add&ad=730882
        self.assertEqual(dt1.toordinal(), 730_882 - 1)

    def test_toordinal04(self):
        # https://www.timeanddate.com/date/dateadded.html?d1=1&m1=1&y1=1&type=add&ad=730911
        self.assertEqual(dt3.toordinal(), 730_911 - 1)

    def test_weekday00(self):
        self.assertEqual(dt1.weekday(), d1.weekday())

    def test_timestamp00(self):
        with LocalTz("Europe/Rome"):
            if LOCALTZ:
                self.assertEqual(d1t1.timestamp(), 1012499103.001234)
            else:
                self.assertRaises(NotImplementedError, d1t1.timestamp)

    def test_timestamp01(self):
        self.assertEqual(d1t1z.timestamp(), 1012506303.001234)

    def test_timestamp02(self):
        with LocalTz("Europe/Rome"):
            dt = datetime(2010, 3, 28, 2, 30)  # doens't exist
            if LOCALTZ:
                self.assertEqual(dt.timestamp(), 1269739800.0)
            else:
                self.assertRaises(NotImplementedError, dt.timestamp)

    def test_timestamp03(self):
        with LocalTz("Europe/Rome"):
            dt = datetime(2010, 8, 10, 2, 30)
            if LOCALTZ:
                self.assertEqual(dt.timestamp(), 1281400200.0)
            else:
                self.assertRaises(NotImplementedError, dt.timestamp)

    def test_timestamp04(self):
        with LocalTz("Europe/Rome"):
            dt = datetime(2010, 10, 31, 2, 30, fold=0)
            if LOCALTZ:
                self.assertEqual(dt.timestamp(), 1288485000.0)
            else:
                self.assertRaises(NotImplementedError, dt.timestamp)

    def test_timestamp05(self):
        with LocalTz("Europe/Rome"):
            dt = datetime(2010, 10, 31, 2, 30, fold=1)
            if LOCALTZ:
                self.assertEqual(dt.timestamp(), 1288488600.0)
            else:
                self.assertRaises(NotImplementedError, dt.timestamp)

    def test_timestamp06(self):
        with LocalTz("US/Eastern"):
            dt = datetime(2020, 3, 8, 2, 30)  # doens't exist
            if LOCALTZ:
                self.assertEqual(dt.timestamp(), 1583652600.0)
            else:
                self.assertRaises(NotImplementedError, dt.timestamp)

    def test_timestamp07(self):
        with LocalTz("US/Eastern"):
            dt = datetime(2020, 8, 10, 2, 30)
            if LOCALTZ:
                self.assertEqual(dt.timestamp(), 1597041000.0)
            else:
                self.assertRaises(NotImplementedError, dt.timestamp)

    def test_timestamp08(self):
        with LocalTz("US/Eastern"):
            dt = datetime(2020, 11, 1, 2, 30, fold=0)
            if LOCALTZ:
                self.assertEqual(dt.timestamp(), 1604215800.0)
            else:
                self.assertRaises(NotImplementedError, dt.timestamp)

    def test_timestamp09(self):
        with LocalTz("US/Eastern"):
            dt = datetime(2020, 11, 1, 2, 30, fold=1)
            if LOCALTZ:
                self.assertEqual(dt.timestamp(), 1604215800.0)
            else:
                self.assertRaises(NotImplementedError, dt.timestamp)

    def test_isoweekday00(self):
        self.assertEqual(dt1.isoweekday(), d1.isoweekday())

    def test_isoformat00(self):
        self.assertEqual(dt3.isoformat(), "2002-03-01T12:59:59.000100+01:00")

    def test_isoformat01(self):
        self.assertEqual(dt3.isoformat("T"), "2002-03-01T12:59:59.000100+01:00")

    def test_isoformat02(self):
        self.assertEqual(dt3.isoformat(" "), "2002-03-01 12:59:59.000100+01:00")

    def test_isoformat03(self):
        self.assertEqual(str(dt3), "2002-03-01 12:59:59.000100+01:00")

    @unittest.skipIf(STDLIB, "standard datetime differs")
    def test___repr__00(self):
        self.assertEqual(repr(dt1), dt1r)

    @unittest.skipIf(STDLIB, "standard datetime differs")
    def test___repr__01(self):
        self.assertEqual(repr(dt3), dt3r)

    @unittest.skipIf(STDLIB, "standard datetime differs")
    def test___repr__02(self):
        self.assertEqual(repr(dt4), dt4r)

    def test___repr__03(self):
        self.assertEqual(dt1, eval_mod(repr(dt1)))

    def test___repr__04(self):
        self.assertEqual(dt3, eval_mod(repr(dt3)))

    def test___repr__05(self):
        self.assertEqual(dt4, eval_mod(repr(dt4)))

    def test___hash__00(self):
        self.assertEqual(dt1, dt5)
        self.assertEqual(hash(dt1), hash(dt5))

    def test___hash__01(self):
        dd1 = dt1 + timedelta(weeks=7)
        dd5 = dt5 + timedelta(days=7 * 7)
        self.assertEqual(hash(dd1), hash(dd5))

    def test___hash__02(self):
        d = {dt1: 1}
        d[dt5] = 2
        self.assertEqual(len(d), 1)
        self.assertEqual(d[dt1], 2)

    def test___hash__03(self):
        self.assertNotEqual(dt1, dt1z1)
        self.assertNotEqual(hash(dt1), hash(dt1z1))

    def test___hash__04(self):
        self.assertNotEqual(dt1z1, dt5z2)
        self.assertNotEqual(hash(dt1z1), hash(dt5z2))

    @unittest.skipIf(STDLIB, "standard datetime has no tuple()")
    def test_tuple00(self):
        self.assertEqual(dt1.tuple(), (2002, 1, 31, 0, 0, 0, 0, None, 0))

    @unittest.skipIf(STDLIB, "standard datetime has no tuple()")
    def test_tuple01(self):
        self.assertEqual(dt27tz2.tuple(), (2010, 3, 27, 12, 0, 0, 0, tz2, 0))

    @unittest.skipIf(STDLIB, "standard datetime has no tuple()")
    def test_tuple02(self):
        self.assertEqual(dt28tz2.tuple(), (2010, 3, 28, 12, 0, 0, 0, tz2, 0))


if __name__ == "__main__":
    unittest.main()
