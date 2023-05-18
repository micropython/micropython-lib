"""Additions to the TarFile class to support creating and appending tar files.

The methods defined below in the TarInfoWrite and TarFileWrite are actually
copied into the correspodning TarInfo and TarFile classes from the utarfile
module.
"""

import uctypes
import os

# Extended subset of tar header fields including the ones we'll write.
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

# Following https://github.com/python/cpython/blob/3.11/Lib/tarfile.py
NUL = b"\0"  # the null character
BLOCKSIZE = 512  # length of processing blocks
RECORDSIZE = BLOCKSIZE * 20  # length of records

# Duplicated from utarfile.py.
DIRTYPE = "dir"
REGTYPE = "file"

# Constants for TarInfo.isdir, isreg.
_S_IFMT = 0o170000
_S_IFREG = 0o100000
_S_IFDIR = 0o040000


def _setstring(b, s, maxlen):
    """Write a string into a bytearray by copying each byte."""
    for i, c in enumerate(s.encode("utf-8")[:maxlen]):
        b[i] = c


class TarInfoWrite:
    added_methods = ["_from_stat", "isdir", "isreg"]
  
    def _from_stat(self, stat):
        """Extended TarInfo for use by utarfile-write."""
        # stat is return from os.stat.
        self.mode = stat[0]
        # Overwrite name-based type inference using mode bits.
        self.type = DIRTYPE if self.isdir() else REGTYPE
        self.uid = stat[4]
        self.gid = stat[5]
        self.size = stat[6]
        self.mtime = stat[8]
        
    def isdir(self):
        return (self.mode & _S_IFMT) == _S_IFDIR

    def isreg(self):
        return (self.mode & _S_IFMT) == _S_IFREG


class TarFileWrite:
    added_methods = [
      "_open_write", "__enter__", "__exit__", "addfile", "add", "close"
    ]

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

    def __enter__(self):
        """Make usable with "with" statement."""
        return self

    def __exit__(self, unused_type, unused_value, unused_traceback):
        """Make usable with "with" statement."""
        self.close()

    def addfile(self, tarinfo, fileobj=None):
        # Write the header: 100 bytes of name, 8 bytes of mode in octal...
        buf = bytearray(BLOCKSIZE)
        name = tarinfo.name
        size = tarinfo.size
        if tarinfo.isdir():
            size = 0
            if not name.endswith("/"):
                name += "/"
        hdr = uctypes.struct(
          uctypes.addressof(buf), TAR_HEADER, uctypes.LITTLE_ENDIAN
        )
        _setstring(hdr.name, name, 100)
        _setstring(hdr.mode, "%06o " % (tarinfo.mode & 0o7777), 7)
        _setstring(hdr.uid, "%06o " % tarinfo.uid, 7)
        _setstring(hdr.gid, "%06o " % tarinfo.gid, 7)
        _setstring(hdr.size, "%011o " % size, 12)
        _setstring(hdr.mtime, "%011o " % tarinfo.mtime, 12)
        _setstring(hdr.typeflag, "5" if tarinfo.isdir() else "0", 1)
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
        # self.TarInfo will exist when this method is pasted into TarFile.
        tarinfo = self.TarInfo(name)
        try:
            tarinfo._from_stat(os.stat(name))
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
