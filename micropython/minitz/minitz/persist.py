import datetime
import os
import struct
import time
from . import Database, tzwrap
from .fetch import fetch_zone, fetch_all

_local_zone_name = 'UTC'
_whole_db = False

_db = None
_last_modified = None
_local_zone = None
_local_tzinfo = datetime.timezone.utc

_last_check = None

path_for_meta_file = 'tzmeta'
path_for_db_file = 'tzdata'

# Initialise by reading from persistent storage.
def init(want_zone_name=None, want_whole_db=None):
    try:
        with open(path_for_meta_file, 'rb') as fp:
            last_modified, data_crc = struct.unpack('<QI', fp.read(12))
            local_zone_name = fp.read().decode()

        if not local_zone_name:
            # Corrupt file:
            # Mode should be 1 or 2.
            # Zone name is mandatory.
            raise ValueError()
        if last_modified == 0:
            last_modified = None

        with open(path_for_db_file, 'rb') as fp:
            data = fp.read()
        
        db = Database(data)
        if db.kind != 1 and db.kind != 2:
            raise ValueError()
        if db.crc != data_crc:
            # The tzdata and tzmeta files do not match.
            raise ValueError()

        whole_db = (db.kind == 2)
        if want_whole_db is not None and want_whole_db != whole_db:
            # Want to download one zone file only, have whole DB
            # OR want to download whole DB, only have one zone
            raise ValueError()

        if want_zone_name is not None and want_zone_name != local_zone_name:
            if not whole_db:
                # Need to download correct zone file.
                raise ValueError()
            local_zone_name = want_zone_name

        # For a TZIF file, the string passed to get_zone_by_name() is ignored.
        local_zone = db.get_zone_by_name(local_zone_name)
        local_tzinfo = tzwrap(local_zone)

        # Success.
        success = True
    except:
        # Failed
        success = False
        
        db = None
        last_modified = None
        local_zone_name = want_zone_name or 'UTC'
        whole_db = whole_db or False
        local_zone = None
        local_tzinfo = datetime.timezone.utc if local_zone_name == 'UTC' else None
    
    # Save state.
    global _local_zone_name, _whole_db, _db, _last_modified, _local_zone, _local_tzinfo, _last_check
    _local_zone_name = local_zone_name
    _whole_db = whole_db
    _db = db
    _last_modified = last_modified
    _local_zone = local_zone
    _local_tzinfo = local_tzinfo
    _last_check = None
    if success:
        # Pretend last check was 23.5 hours ago.
        # That way the next check will be in 30 minutes.
        # This means that if there are many reboots in a row, we don't flood
        # the server with requests.
        # 23.5 * 3600 * 1000 = 84_600_000
        #
        # (It would be better if we could use real UTC time to track when the
        # last check was, and store the last update time in persistent memory.
        # But we don't necessarily know the real UTC time at init time, and may
        # not want a Flash write on every update check).
        _last_check = time.ticks_add(time.ticks_ms(), -84_600_000)

    return success


def _force_update_from_internet(zone_name=None, whole_db=None, timeout=None):
    last_modified = _last_modified
    if whole_db is None:
        whole_db = _whole_db
    elif whole_db != _whole_db:
        # Force fresh download as it's a different file
        last_modified = None
    if zone_name is None:
        zone_name = _local_zone_name
    elif zone_name != _local_zone_name and not whole_db:
        # Force fresh download as it's a different file
        last_modified = None
    if not zone_name:
        # Empty string is not a valid zone name.
        raise ValueError()

    # We update _last_check even if the HTTP request fails.
    # This is to comply with the fair usage policy of tzdata.net.
    global _last_check
    _last_check = time.ticks_ms()

    if whole_db:
        last_modified, data = fetch_zone(zone_name, last_modified, timeout)
    else:
        last_modified, data = fetch_all(last_modified, timeout)

    if data is None:
        # Not changed
        return

    db = Database(data)
    if db.kind != (2 if whole_db else 1):
        # Not the kind of file that was expected
        raise ValueError()

    # For a TZIF file, the string passed to get_zone_by_name() is ignored.
    local_zone = db.get_zone_by_name(zone_name)
    local_tzinfo = tzwrap(local_zone)

    # Download success!

    # Save state.
    global _local_zone_name, _whole_db, _db, _last_modified, _local_zone, _local_tzinfo
    _local_zone_name = zone_name
    _whole_db = whole_db
    _db = db
    _last_modified = last_modified
    _local_zone = local_zone
    _local_tzinfo = local_tzinfo

    # Save the data to persistent storage.

    # Maybe this may make flash wear-levelling easier?
    # We give the filesystem as much free space as possible
    # before we start writing to it.
    os.unlink(path_for_db_file)

    with open(path_for_meta_file, 'wb') as fp:
        fp.write(struct.pack('<QI', last_modified or 0, db.crc))
        fp.write(zone_name.encode())

    with open(path_for_db_file, 'wb') as fp:
        fp.write(data)


# Initialise by reading from persistent storage.
# If that fails, will try to do first-time download of timezone
# data from the Internet.
def init_with_download_if_needed(zone_name=None, whole_db=None, timeout=None):
    if not init(zone_name, whole_db):
        if whole_db or zone_name != 'UTC':
            _force_update_from_internet(zone_name, whole_db, timeout)


def set_zone(zone_name, can_download, timeout=None):
    if _local_zone_name == zone_name:
        # Nothing to do!
        pass
    elif _whole_db:
        local_zone = _db.get_zone_by_name(zone_name)
        local_tzinfo = tzwrap(local_zone)
            
        global _local_zone_name, _local_zone, _local_tzinfo
        _local_zone_name = zone_name
        _local_zone = local_zone
        _local_tzinfo = local_tzinfo
    elif not can_download:
        raise ValueError("Changing zone without whole DB or Internet")
    else:
        _force_update_from_internet(zone_name, _whole_db, timeout)


def update_from_internet_if_needed(timeout=None):
    # Call this regularly.  Ideally at least once an hour, but it's fine
    # to call it much more frequently, even multiple times per second.
    # This function will do nothing if an update is not needed.
    #
    # We attempt an Internet update at most once per day.
    # This is to comply with the fair usage policy of tzdata.net.
    if (_last_check is not None and
        time.ticks_diff(time.ticks_ms(), _last_check) < 24 * 3600 * 1000):
        # Too soon.
        return
    _force_update_from_internet(timeout=timeout)


def has_tzinfo():
    return _local_tzinfo is not None

def get_tzinfo():
    if _local_tzinfo is None:
        raise ValueError()
    return _local_tzinfo

def have_db():
    return _db is not None

def get_raw_zone():
    if _local_zone is None:
        raise ValueError()
    return _local_zone

def get_db():
    if _db is None:
        raise ValueError()
    return _db

def get_zone_name():
    return _local_zone_name

def get_last_modified():
    return datetime.datetime.fromtimestamp(_last_modified, datetime.timezone.utc)
