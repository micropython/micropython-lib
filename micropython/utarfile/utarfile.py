import uctypes
import os  # For reading files when writing tar files.

# http://www.gnu.org/software/tar/manual/html_node/Standard.html
TAR_HEADER = {
    "name": (uctypes.ARRAY | 0, uctypes.UINT8 | 100),
    "mode": (uctypes.ARRAY | 100, uctypes.UINT8 | 7),
    "uid": (uctypes.ARRAY | 108, uctypes.UINT8 | 7),
    "gid": (uctypes.ARRAY | 116, uctypes.UINT8 | 7),
    "size": (uctypes.ARRAY | 124, uctypes.UINT8 | 12),
    "mtime": (uctypes.ARRAY | 136, uctypes.UINT8 | 12),
    "chksum": (uctypes.ARRAY | 148, uctypes.UINT8 | 8),
    "typeflag": (uctypes.ARRAY | 156, uctypes.UINT8 | 1),
}

DIRTYPE = "dir"
REGTYPE = "file"

# Following https://github.com/python/cpython/blob/3.11/Lib/tarfile.py
NUL = b"\0"  # the null character
BLOCKSIZE = 512  # length of processing blocks
RECORDSIZE = BLOCKSIZE * 20  # length of records


def roundup(val, align):
    return (val + align - 1) & ~(align - 1)


class FileSection:
    def __init__(self, f, content_len, aligned_len):
        self.f = f
        self.content_len = content_len
        self.align = aligned_len - content_len

    def read(self, sz=65536):
        if self.content_len == 0:
            return b""
        if sz > self.content_len:
            sz = self.content_len
        data = self.f.read(sz)
        sz = len(data)
        self.content_len -= sz
        return data

    def readinto(self, buf):
        if self.content_len == 0:
            return 0
        if len(buf) > self.content_len:
            buf = memoryview(buf)[: self.content_len]
        sz = self.f.readinto(buf)
        self.content_len -= sz
        return sz

    def skip(self):
        sz = self.content_len + self.align
        if sz:
            buf = bytearray(16)
            while sz:
                s = min(sz, 16)
                self.f.readinto(buf, s)
                sz -= s


class TarInfo:
    def __str__(self):
        return "TarInfo(%r, %s, %d)" % (self.name, self.type, self.size)


def _setstring(b, s, maxlen):
    """Write a string into a bytearray by copying each byte."""
    for i, c in enumerate(s.encode("utf-8")[:maxlen]):
        b[i] = c


_S_IFMT = 0o170000
_S_IFREG = 0o100000
_S_IFDIR = 0o040000


def _isdir(finfo):
    return (finfo[0] & _S_IFMT) == _S_IFDIR


def _isreg(finfo):
    return (finfo[0] & _S_IFMT) == _S_IFREG


class TarFile:
    def __init__(self, name=None, mode="r", fileobj=None):
        modes = {"r": "rb", "w": "wb"}
        if mode not in modes:
            raise ValueError("mode must be 'r' or 'w'")
        if fileobj:
            self.f = fileobj
        else:
            self.f = open(name, modes[mode])
        self.subf = None
        self.mode = mode
        self.offset = 0

    def next(self):
        if self.subf:
            self.subf.skip()
        buf = self.f.read(BLOCKSIZE)
        if not buf:
            return None
        self.offset += len(buf)

        h = uctypes.struct(uctypes.addressof(buf), TAR_HEADER, uctypes.LITTLE_ENDIAN)

        # Empty block means end of archive
        if h.name[0] == 0:
            return None

        d = TarInfo()
        d.name = str(h.name, "utf-8").rstrip("\0")
        d.size = int(bytes(h.size), 8)
        d.type = [REGTYPE, DIRTYPE][d.name[-1] == "/"]
        self.subf = d.subf = FileSection(self.f, d.size, roundup(d.size, BLOCKSIZE))
        self.offset += roundup(d.size, BLOCKSIZE)
        return d

    def __iter__(self):
        return self

    def __next__(self):
        v = self.next()
        if v is None:
            raise StopIteration
        return v

    def extractfile(self, tarinfo):
        return tarinfo.subf

    def addfile(self, tarinfo, fileobj=None):
        # Write the header: 100 bytes of name, 8 bytes of mode in octal...
        buf = bytearray(BLOCKSIZE)
        name = tarinfo.name
        finfo = tarinfo.finfo
        size = finfo[6]
        if _isdir(finfo):
            size = 0
            if not name.endswith("/"):
                name += "/"
        hdr = uctypes.struct(uctypes.addressof(buf), TAR_HEADER, uctypes.LITTLE_ENDIAN)
        _setstring(hdr.name, name, 100)
        _setstring(hdr.mode, "%06o " % (finfo[0] & 0o7777), 7)
        _setstring(hdr.uid, "%06o " % finfo[4], 7)
        _setstring(hdr.gid, "%06o " % finfo[5], 7)
        _setstring(hdr.size, "%011o " % size, 12)
        _setstring(hdr.mtime, "%011o " % finfo[8], 12)
        _setstring(hdr.typeflag, "5" if _isdir(finfo) else "0", 1)
        # Checksum is calculated with checksum field all blanks.
        _setstring(hdr.chksum, " " * 8, 8)
        # Calculate and insert the actual checksum.
        chksum = sum(buf)
        _setstring(hdr.chksum, "%06o\0" % chksum, 7)
        # Emit the header.
        self.f.write(buf)
        self.offset += len(buf)

        # Copy the file contents, if any.
        if fileobj:
            n_bytes = self.f.write(fileobj.read())
            self.offset += n_bytes
            remains = -n_bytes & (BLOCKSIZE - 1)  # == 0b111111111
            if remains:
                buf = bytearray(remains)
                self.f.write(buf)
                self.offset += len(buf)

    def add(self, name, recursive=True):
        tarinfo = TarInfo()
        tarinfo.name = name
        try:
            tarinfo.finfo = os.stat(name)
        except OSError:
            print("Cannot stat", name, " - skipping.")
            return
        if not (_isdir(tarinfo.finfo) or _isreg(tarinfo.finfo)):
            # We only accept directories or regular files.
            print(name, "is not a directory or regular file - skipping.")
            return
        tarinfo.type = DIRTYPE if _isdir(tarinfo.finfo) else REGTYPE
        if tarinfo.type == DIRTYPE:
            self.addfile(tarinfo)
            if recursive:
                for f in os.ilistdir(name):
                    self.add(name + "/" + f[0], recursive)
        else:  # type == REGTYPE
            self.addfile(tarinfo, open(name, "rb"))

    def close(self):
        # Must be called to complete writing a tar file.
        if self.mode == "w":
            self.f.write(NUL * (BLOCKSIZE * 2))
            self.offset += BLOCKSIZE * 2
            remainder = self.offset % RECORDSIZE
            if remainder:
                self.f.write(NUL * (RECORDSIZE - remainder))
        self.f.close()
        self.f = None
