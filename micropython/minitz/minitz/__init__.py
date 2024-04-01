from _minitz import Database
import datetime as _datetime


# Wraps a _minitz.Zone, and implements tzinfo
class tzwrap(_datetime.tzinfo):
    def __init__(self, mtz_zone):
        self._mtz_zone = mtz_zone

    def __str__(self):
        return self.tzname(None)

    # Returns (offset: int, designator: str, is_dst: int)
    def _lookup_local(self, dt):
        if dt.tzinfo is not self:
            raise ValueError()
        t = dt.replace(tzinfo=_datetime.timezone.utc, fold=0).timestamp()
        return self._mtz_zone.lookup_local(t, dt.fold)

    def utcoffset(self, dt):
        return _datetime.timedelta(seconds=self._lookup_local(dt)[0])

    def is_dst(self, dt):
        # Nonstandard.  Returns bool.
        return bool(self._lookup_local(dt)[2])

    def dst(self, dt):
        is_dst = self._lookup_local(dt)[2]
        # TODO in the case of is_dst=1, this is returning
        # a made-up value that may be wrong.
        return _datetime.timedelta(hours=is_dst)

    def tzname(self, dt):
        return self._lookup_local(dt)[1]

    def fromutc(self, dt):
        if dt.fold != 0:
            raise ValueError()
        t = dt.replace(tzinfo=_datetime.timezone.utc).timestamp()
        offset = self._mtz_zone.lookup_utc(t)[0]
        _datetime.timedelta(seconds=offset)

        return dt + self._offset
