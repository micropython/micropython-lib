# test_suntime.py

import unittest
from suntime import Suntime, Sundatetime

pl1 = ( 42.5966460,  12.4360233)
pl2 = ( 51.1627938,-122.9593616)
pl3 = (-33.9252192,  18.4240762)
pl4 = ( 55.1574890,  82.8547661)
pl5 = ( 78.6560170,  16.3447384)
pl6 = pl5
pl7 = (-77.7817838, 166.4561470)
pl8 = pl7

dt1 = (2000,  1,  1)
dt2 = (2014, 10,  3)
dt3 = (2016, 12, 21)
dt4 = (2021,  4, 24)
dt5 = (2040,  8, 25)
dt6 = (2040,  8, 26)
dt7 = (2033,  8, 10)
dt8 = (2033, 10, 21)

tz1 = ( 1, 0)
tz2 = (-8, 1)
tz3 = ( 2, 0)
tz4 = ( 0, 0)
tz5 = ( 1, 1)
tz6 = ( 1, 1)
tz7 = (13,-1)
tz8 = (13, 0)

from datetime import datetime, timedelta, timezone

class Tz(timezone):
    def __init__(self, hours, dst=0):
        super().__init__(timedelta(hours=hours))
        self._dst = dst

    def dst(self, dt):
        return timedelta(hours=self._dst) if self.isdst(dt) else timedelta(0)

    def isdst(self, dt):
        return self._dst != 0

class TestSunTime(unittest.TestCase):

    def test_suntime1(self):
        st1 = Suntime(*pl1, timezone=tz1[0]*60)
        st1.calc_sunrise_sunset(*dt1, dst=tz1[1]*60)
        self.assertEqual(divmod(st1.sunrise, 60), ( 7, 40))
        self.assertEqual(divmod(st1.sunset , 60), (16, 47))
        self.assertFalse(st1.is_daytime( 0*60 +  0))
        self.assertTrue (st1.is_daytime(12*60 +  0))
        self.assertTrue (st1.is_sunrise( 7*60 + 40))
        self.assertTrue (st1.is_sunset (16*60 + 47))
        self.assertIsNone(st1.is_daytime  (  -1))
        self.assertIsNone(st1.is_daytime  (1440))
        self.assertIsNone(st1.is_nighttime(  -1))
        self.assertIsNone(st1.is_nighttime(1440))

    def test_suntime2(self):
        st2 = Suntime(*pl2, timezone=tz2[0]*60)
        st2.calc_sunrise_sunset(*dt2, dst=tz2[1]*60)
        self.assertEqual(divmod(st2.sunrise, 60), ( 7, 16))
        self.assertEqual(divmod(st2.sunset , 60), (18, 46))
        self.assertFalse(st2.is_daytime( 0*60 +  0))
        self.assertTrue (st2.is_daytime(12*60 +  0))
        self.assertTrue (st2.is_sunrise( 7*60 + 16))
        self.assertTrue (st2.is_sunset (18*60 + 46))

    def test_suntime3(self):
        st3 = Suntime(*pl3, timezone=tz3[0]*60)
        st3.calc_sunrise_sunset(*dt3, dst=tz3[1]*60)
        self.assertEqual(divmod(st3.sunrise, 60), ( 5, 32))
        self.assertEqual(divmod(st3.sunset , 60), (19, 57))
        self.assertFalse(st3.is_daytime( 0*60 +  0))
        self.assertTrue (st3.is_daytime(12*60 +  0))
        self.assertTrue (st3.is_sunrise( 5*60 + 32))
        self.assertTrue (st3.is_sunset (19*60 + 57))

    def test_suntime4(self):
        st4 = Suntime(*pl4, timezone=tz4[0]*60)
        st4.calc_sunrise_sunset(*dt4, dst=tz4[1]*60)
        self.assertEqual(divmod(st4.sunrise, 60), (-1,  4))
        self.assertEqual(divmod(st4.sunset , 60), (13, 49))

    def test_suntime5(self):
        st5 = Suntime(*pl5, timezone=tz5[0]*60)
        st5.calc_sunrise_sunset(*dt5, dst=tz5[1]*60)
        self.assertEqual(divmod(st5.sunrise, 60), (-12, 57))
        self.assertEqual(divmod(st5.sunset , 60), ( 36, 57))
        self.assertTrue (st5.is_daytime  (  0*60 +  0))
        self.assertFalse(st5.is_nighttime( 12*60 +  0))
        self.assertFalse(st5.is_sunrise  (-12*60 + 57))
        self.assertFalse(st5.is_sunset   ( 36*60 + 57))

    def test_suntime6(self):
        st6 = Suntime(*pl6, timezone=tz6[0]*60)
        st6.calc_sunrise_sunset(*dt6, dst=tz6[1]*60)
        self.assertEqual(divmod(st6.sunrise, 60), ( 1, 35))
        self.assertEqual(divmod(st6.sunset , 60), (24, 18))
        self.assertTrue (st6.is_sunrise( 1*60 + 35))
        self.assertFalse(st6.is_sunset (24*60 + 18))

    def test_suntime7(self):
        st7 = Suntime(*pl7, timezone=tz7[0]*60)
        st7.calc_sunrise_sunset(*dt7, dst=tz7[1]*60)
        self.assertEqual(divmod(st7.sunrise, 60), ( 37, 0))
        self.assertEqual(divmod(st7.sunset , 60), (-11, 0))
        self.assertFalse(st7.is_daytime  ( 12*60 + 0))
        self.assertTrue (st7.is_nighttime( 12*60 + 0))
        self.assertFalse(st7.is_sunrise  ( 37*60 + 0))
        self.assertFalse(st7.is_sunset   (-11*60 + 0))

    def test_suntime8(self):
        st8 = Suntime(*pl8, timezone=tz8[0]*60)
        st8.calc_sunrise_sunset(*dt8, dst=tz8[1]*60)
        self.assertEqual(divmod(st8.sunrise, 60), ( 3,  6))
        self.assertEqual(divmod(st8.sunset , 60), (24, 12))
        self.assertTrue (st8.is_daytime  (12*60 +  6))
        self.assertFalse(st8.is_nighttime(23*60 + 59))
        self.assertTrue (st8.is_sunrise  ( 3*60 +  6))
        self.assertFalse(st8.is_sunset   (24*60 + 12))

    def test_sundatetime1(self):
        tz = Tz(*tz1)
        sd1 = Sundatetime(*pl1)
        sd1.calc_sunrise_sunset(datetime(*dt1, tzinfo=tz))
        self.assertEqual(sd1.sunrise.tuple(),   (2000, 1, 1,  7, 40, 0, tz) )
        self.assertEqual(sd1.sunset .tuple(),   (2000, 1, 1, 16, 47, 0, tz) )
        self.assertFalse(sd1.is_daytime(datetime(2000, 1, 1,  0,  0, 0, tz)))
        self.assertTrue (sd1.is_daytime(datetime(2000, 1, 1, 12,  0, 0, tz)))
        self.assertTrue (sd1.is_sunrise(datetime(2000, 1, 1,  7, 40, 0, tz)))
        self.assertTrue (sd1.is_sunset (datetime(2000, 1, 1, 16, 47, 0, tz)))

    def test_sundatetime2(self):
        tz = Tz(*tz2)
        sd2 = Sundatetime(*pl2)
        sd2.calc_sunrise_sunset(datetime(*dt2, tzinfo=tz))
        self.assertEqual(sd2.sunrise.tuple(),   (2014, 10, 3,  7, 16, 0, tz))
        self.assertEqual(sd2.sunset .tuple(),   (2014, 10, 3, 18, 46, 0, tz))
        self.assertFalse(sd2.is_daytime(datetime(2014, 10, 3,  0,  0, 0, tz)))
        self.assertTrue (sd2.is_daytime(datetime(2014, 10, 3, 12,  0, 0, tz)))
        self.assertTrue (sd2.is_sunrise(datetime(2014, 10, 3,  7, 16, 0, tz)))
        self.assertTrue (sd2.is_sunset (datetime(2014, 10, 3, 18, 46, 0, tz)))

    def test_sundatetime3(self):
        tz = Tz(*tz3)
        sd3 = Sundatetime(*pl3)
        sd3.calc_sunrise_sunset(datetime(*dt3, tzinfo=tz))
        self.assertEqual(sd3.sunrise.tuple(),   (2016, 12, 21,  5, 32, 0, tz))
        self.assertEqual(sd3.sunset .tuple(),   (2016, 12, 21, 19, 57, 0, tz))
        self.assertFalse(sd3.is_daytime(datetime(2016, 12, 21,  0,  0, 0, tz)))
        self.assertTrue (sd3.is_daytime(datetime(2016, 12, 21, 12,  0, 0, tz)))
        self.assertTrue (sd3.is_sunrise(datetime(2016, 12, 21,  5, 32, 0, tz)))
        self.assertTrue (sd3.is_sunset (datetime(2016, 12, 21, 19, 57, 0, tz)))

    def test_sundatetime4(self):
        tz = Tz(*tz4)
        sd4 = Sundatetime(*pl4)
        sd4.calc_sunrise_sunset(datetime(*dt4, tzinfo=tz))
        self.assertEqual(sd4.sunrise.tuple(),   (2021, 4, 23, 23,  4, 0, tz))
        self.assertEqual(sd4.sunset .tuple(),   (2021, 4, 24, 13, 49, 0, tz))

    def test_sundatetime5(self):
        tz = Tz(*tz5)
        sd5 = Sundatetime(*pl5)
        sd5.calc_sunrise_sunset(datetime(*dt5, tzinfo=tz))
        self.assertEqual(sd5.sunrise.tuple(),     (2040, 8, 24, 12, 57, 0, tz))
        self.assertEqual(sd5.sunset .tuple(),     (2040, 8, 26, 12, 57, 0, tz))
        self.assertTrue (sd5.is_daytime  (datetime(2040, 8, 25,  0,  0, 0, tz)))
        self.assertFalse(sd5.is_nighttime(datetime(2040, 8, 25, 12,  0, 0, tz)))
        self.assertTrue (sd5.is_sunrise  (datetime(2040, 8, 24, 12, 57, 0, tz)))
        self.assertTrue (sd5.is_sunset   (datetime(2040, 8, 26, 12, 57, 0, tz)))

    def test_sundatetime6(self):
        tz = Tz(*tz6)
        sd6 = Sundatetime(*pl6)
        sd6.calc_sunrise_sunset(datetime(*dt6, tzinfo=tz))
        self.assertEqual(sd6.sunrise.tuple(),   (2040, 8, 26, 1, 35, 0, tz))
        self.assertEqual(sd6.sunset .tuple(),   (2040, 8, 27, 0, 18, 0, tz))
        self.assertTrue (sd6.is_sunrise(datetime(2040, 8, 26, 1, 35, 0, tz)))
        self.assertTrue (sd6.is_sunset (datetime(2040, 8, 27, 0, 18, 0, tz)))

    def test_sundatetime7(self):
        tz = Tz(*tz7)
        sd7 = Sundatetime(*pl7)
        sd7.calc_sunrise_sunset(datetime(*dt7, tzinfo=tz))
        self.assertEqual(sd7.sunrise.tuple(),     (2033, 8, 11, 13, 0, 0, tz))
        self.assertEqual(sd7.sunset .tuple(),     (2033, 8,  9, 13, 0, 0, tz))
        self.assertFalse(sd7.is_daytime  (datetime(2033, 8, 11, 12, 0, 0, tz)))
        self.assertFalse(sd7.is_nighttime(datetime(2033, 8, 25,  0, 0, 0, tz)))
        self.assertFalse(sd7.is_sunrise  (datetime(2033, 8, 11, 13, 0, 0, tz)))
        self.assertFalse(sd7.is_sunset   (datetime(2033, 8,  9, 13, 0, 0, tz)))

    def test_sundatetime8(self):
        tz = Tz(*tz8)
        sd8 = Sundatetime(*pl8)
        sd8.calc_sunrise_sunset(datetime(*dt8, tzinfo=tz))
        self.assertEqual(sd8.sunrise.tuple(),     (2033, 10, 21,  3,  6, 0, tz))
        self.assertEqual(sd8.sunset .tuple(),     (2033, 10, 22,  0, 12, 0, tz))
        self.assertTrue (sd8.is_daytime  (datetime(2033, 10, 21, 12,  6, 0, tz)))
        self.assertFalse(sd8.is_nighttime(datetime(2033, 10, 21, 23, 59, 0, tz)))
        self.assertTrue (sd8.is_sunrise  (datetime(2033, 10, 21,  3,  6, 0, tz)))
        self.assertTrue (sd8.is_sunset   (datetime(2033, 10, 22,  0, 12, 0, tz)))

if __name__ == '__main__':
        unittest.main()
