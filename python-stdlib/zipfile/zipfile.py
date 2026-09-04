import io
import struct

try:
    import deflate

    _has_deflate = True
except ImportError:
    _has_deflate = False


class BadZipFile(Exception):
    pass


_MAGIC = const(b"\x50\x4b\x03\x04")


ZIP_STORED = const(0)
ZIP_DEFLATED = const(8)


class _ZipIO(io.IOBase):
    def __init__(self, inner, length):
        self._i = inner
        self._o = 0  # virtual offset
        self._l = length  # max virtual offset
        self._b = inner.tell()  # min physical offset
        self._e = self._b + length  # max physical offset

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self):
        if self._i is not None:
            self._i = None

    def read(self, size=-1):
        if self._i is None:
            raise ValueError
        physical_offset = self._o + self._b
        if size < 0:
            size = self._e - physical_offset
        else:
            size = min(self._e - physical_offset, size)
        if size <= 0:
            return b""
        old_offset = self._i.tell()
        try:
            self._i.seek(self._o + self._b)
            data = self._i.read(size)
        finally:
            self._i.seek(old_offset)
        self._o += len(data)
        return data

    def readinto(self, buffer):
        count = 0
        for index in range(len(buffer)):
            byte = self.read(1)
            if byte == b"":
                break
            buffer[index] = byte[0]
            count += 1
        return count

    def tell(self):
        if self._i is None:
            raise ValueError
        return self._o

    def seek(self, offset, whence=0):
        if self._i is None:
            raise ValueError
        if whence == 0:
            new_offset = offset
        elif whence == 1:
            new_offset = self._o + offset
        elif whence == 2:
            new_offset = self._l + offset
        self._o = max(min(new_offset, self._l), 0)
        return self._o


class ZipInfo:
    def __init__(self, filename="NoName", date_time=(1980, 1, 1, 0, 0, 0)):
        self.filename = filename
        self.date_time = date_time
        self.compress_type = None
        self.comment = None
        self.extra = None
        self.create_system = None
        self.create_version = None
        self.extract_version = None
        self.reserved = 0
        self.flag_bits = None
        self.volume = None
        self.internal_attr = None
        self.external_attr = None
        self.header_offset = 0
        self.CRC = 0
        self.compress_size = 0
        self.file_size = 0

    @staticmethod
    def from_file(*args, **kwargs):
        raise NotImplementedError

    def is_dir(self):
        return self.compress_size == 0 and self.file_size == 0 and self.filename.endswith("/")

    def __repr__(self):
        if self.compress_type == ZIP_STORED:
            compress_type = "stored"
        elif self.compress_type == ZIP_DEFLATED:
            compress_type = "deflated"
        else:
            compress_type = str(self.compress_type)
        return "<{} filename={} compress_type={} file_size={} compress_size={}>".format(
            self.__class__.__name__,
            repr(self.filename),
            compress_type,
            self.file_size,
            self.compress_size,
        )


def _iter_files(f):
    if f is None:
        raise ValueError
    f.seek(0)
    while True:
        # 4.3.7 "Local file header"
        offset = f.tell()
        buffer = f.read(30)
        if len(buffer) != 30:
            break
        (
            magic,
            min_version,
            create_sys,
            flags,
            method,
            modification_time,
            modification_date,
            crc32,
            compressed_size,
            uncompressed_size,
            name_length,
            extra_length,
        ) = struct.unpack_from("<IBB4H3IHH", buffer)
        if magic != 0x04034B50:
            break

        if flags & 0b1000:
            # 4.4.4 "General purpose bit flag":
            #
            # "[...] If this bit is set, the fields crc-32, compressed size
            # and uncompressed size are set to zero in the local header.
            # The correct values are put in the data descriptor immediately
            # following the compressed data."
            raise NotImplementedError("data descriptors are not supported")

        name = f.read(name_length)
        if len(name) != name_length:
            raise BadZipFile
        info = ZipInfo(
            name.decode("ascii"),
            (
                (modification_date >> 9) + 1980,
                (modification_date >> 5) & 0x0F,
                modification_date & 0x1F,
                modification_time >> 11,
                (modification_time >> 5) & 0x3F,
                (modification_time & 0x1F) << 1,
            ),
        )
        info.compress_type = method
        info.CRC = crc32
        info.flag_bits = flags
        info.compress_size = compressed_size
        info.file_size = uncompressed_size
        info.header_offset = offset
        info.extract_version = min_version
        info.create_version = min_version
        info.create_system = create_sys
        if extra_length > 0:
            info.extra = f.read(extra_length)
            if len(info.extra) != extra_length:
                raise BadZipFile
        yield info

        # Skip encryption header
        if info.flag_bits & 0b1:
            f.seek(12, 1)
        f.seek(info.compress_size, 1)


def is_zipfile(filename):
    if isinstance(filename, str):
        try:
            with open(filename, "rb") as file:
                return file.read(4) == _MAGIC
        except:
            return False

    offset = filename.tell()
    try:
        return filename.read(4) == _MAGIC
    finally:
        filename.seek(offset)


class ZipFile:
    def __init__(self, file, mode="r", **kwargs):
        if mode != "r":
            raise NotImplementedError
        if isinstance(file, str):
            self.filename = file
            self._f = open(self.filename, "rb")
        else:
            self._f = file
            self.filename = "ZipFile"
        self.debug = 0  # For CPython compatibility
        self.comment = ""  # For CPython compatibility

        # CPython would automatically load and cache the names list, so calling
        # `getinfo`, `infolist`, and `namelist` would still return data even after
        # `close` was called.

    def close(self):
        if self._f:
            self._f.close()
            self._f = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def getinfo(self, name):
        for file in _iter_files(self._f):
            if file.filename == name:
                return file
        raise KeyError

    def infolist(self):
        return list(_iter_files(self._f))

    def namelist(self):
        return [file.filename for file in self.infolist()]

    def open(self, name, mode="r", pwd=None, **kwargs):
        if self._f is None:
            raise ValueError
        if mode != "r" or pwd is not None:
            raise NotImplementedError
        info = self.getinfo(name)
        # bail out if any bits related to encryption, reserved flags, or
        # enhanced compression are set, or if the compression method is
        # unsupported.
        if (
            info.flag_bits & 0b1111000001111001 != 0
            or (info.compress_type == ZIP_DEFLATED and not _has_deflate)
            or (info.compress_type not in (ZIP_STORED, ZIP_DEFLATED))
        ):
            raise NotImplementedError
        stream = _ZipIO(self._f, info.file_size)
        if info.compress_type is ZIP_STORED:
            return stream
        return deflate.DeflateIO(stream, deflate.RAW, 15)

    def extract(self, *args, **kwargs):
        raise NotImplementedError

    def extractall(self, *args, **kwargs):
        raise NotImplementedError

    def printdir(self):
        raise NotImplementedError

    def setpassword(self, *args, **kwargs):
        raise NotImplementedError

    def read(self, name, pwd=None):
        with self.open(name, pwd=pwd) as f:
            return f.read()

    def testzip(self):
        raise NotImplementedError
