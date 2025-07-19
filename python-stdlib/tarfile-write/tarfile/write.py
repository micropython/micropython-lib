"""Additions to the TarFile class to support creating and appending tar files.

The methods defined below in are injected into the TarFile class in the
tarfile package.
"""

import uctypes
import os

# Extended subset of tar header fields including the ones we'll write.
# http://www.gnu.org/software/tar/manual/html_node/Standard.html
_TAR_HEADER = {
    "name": (uctypes.ARRAY | 0, uctypes.UINT8 | 100),
    "mode": (uctypes.ARRAY | 100, uctypes.UINT8 | 8),
    "uid": (uctypes.ARRAY | 108, uctypes.UINT8 | 8),
    "gid": (uctypes.ARRAY | 116, uctypes.UINT8 | 8),
    "size": (uctypes.ARRAY | 124, uctypes.UINT8 | 12),
    "mtime": (uctypes.ARRAY | 136, uctypes.UINT8 | 12),
    "chksum": (uctypes.ARRAY | 148, uctypes.UINT8 | 8),
    "typeflag": (uctypes.ARRAY | 156, uctypes.UINT8 | 1),
}


_NUL = const(b"\0")  # the null character
_BLOCKSIZE = const(512)  # length of processing blocks
_RECORDSIZE = const(_BLOCKSIZE * 20)  # length of records


def _open_write(self, name, mode, fileobj):
    if mode == "w":
        if not fileobj:
            self.f = open(name, "wb")
        else:
            self.f = fileobj
    elif mode == "a":
        if not fileobj:
            self.f = open(name, "r+b")
        else:
            self.f = fileobj
        # Read through the existing file.
        while self.next():
            pass
        # Position at start of end block.
        self.f.seek(self.offset)
    else:
        raise ValueError("mode " + mode + " not supported.")


def _close_write(self):
    # Must be called to complete writing a tar file.
    if self.mode == "w":
        self.f.write(_NUL * (_BLOCKSIZE * 2))
        self.offset += _BLOCKSIZE * 2
        remainder = self.offset % _RECORDSIZE
        if remainder:
            self.f.write(_NUL * (_RECORDSIZE - remainder))


def addfile(self, tarinfo, fileobj=None):
    # Write the header: 100 bytes of name, 8 bytes of mode in octal...
    buf = bytearray(_BLOCKSIZE)
    name = tarinfo.name
    size = tarinfo.size
    if tarinfo.isdir():
        size = 0
        if not name.endswith("/"):
            name += "/"
    hdr = uctypes.struct(uctypes.addressof(buf), _TAR_HEADER, uctypes.LITTLE_ENDIAN)
    hdr.name[:] = name.encode("utf-8")[:100]
    hdr.mode[:] = b"%07o\0" % ((0o755 if tarinfo.isdir() else 0o644) & 0o7777)
    hdr.uid[:] = b"%07o\0" % tarinfo.uid
    hdr.gid[:] = b"%07o\0" % tarinfo.gid
    hdr.size[:] = b"%011o\0" % size
    hdr.mtime[:] = b"%011o\0" % tarinfo.mtime
    hdr.typeflag[:] = b"5" if tarinfo.isdir() else b"0"
    # Checksum is calculated with checksum field all blanks.
    hdr.chksum[:] = b"        "
    # Calculate and insert the actual checksum.
    chksum = sum(buf)
    hdr.chksum[:] = b"%06o\0 " % chksum
    # Emit the header.
    self.f.write(buf)
    self.offset += len(buf)

    # Copy the file contents, if any.
    if fileobj:
        n_bytes = self.f.write(fileobj.read())
        self.offset += n_bytes
        remains = -n_bytes & (_BLOCKSIZE - 1)  # == 0b111111111
        if remains:
            buf = bytearray(remains)
            self.f.write(buf)
            self.offset += len(buf)


def add(self, name, recursive=True):
    from . import TarInfo

    try:
        stat = os.stat(name)
        res_name = (name + '/') if (stat[0] & 0xf000) == 0x4000 else name
        tarinfo = TarInfo(res_name)
        tarinfo.mode = stat[0]
        tarinfo.uid = stat[4]
        tarinfo.gid = stat[5]
        tarinfo.size = stat[6]
        tarinfo.mtime = stat[8]
    except OSError:
        print("Cannot stat", name, " - skipping.")
        return
    if not (tarinfo.isdir() or tarinfo.isreg()):
        # We only accept directories or regular files.
        print(name, "is not a directory or regular file - skipping.")
        return
    if tarinfo.isdir():
        self.addfile(tarinfo)
        if recursive:
            for f in os.ilistdir(name):
                self.add(name + "/" + f[0], recursive)
    else:  # type == REGTYPE
        self.addfile(tarinfo, open(name, "rb"))
