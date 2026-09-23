# The values the built-in errno module provides come from the system headers
# the port was built against, and they differ between operating systems and
# between architectures: ETIMEDOUT is 110 on Linux/x86, 145 on Linux/mips and
# 60 on macOS.  This module must not override them with a table of its own.

import errno

try:
    import uerrno
except ImportError:
    # Built without MICROPY_PY_ERRNO, so there is nothing to compare against.
    print("SKIP")
    raise SystemExit


# Every name the built-in module provides has to come through unchanged.
names = [name for name in dir(uerrno) if name.startswith("E")]
assert names, dir(uerrno)
for name in names:
    theirs = getattr(uerrno, name)
    ours = getattr(errno, name, None)
    assert ours is not None, "errno.%s is missing, uerrno.%s is %d" % (name, name, theirs)
    assert ours == theirs, "errno.%s is %d, uerrno.%s is %d" % (name, ours, name, theirs)

# errorcode has to survive too: mp_errno_to_str() looks names up in it, and it
# is what makes str(OSError(errno.ENOENT)) readable.
if hasattr(uerrno, "errorcode"):
    assert isinstance(errno.errorcode, dict), errno.errorcode
    for code, name in errno.errorcode.items():
        assert getattr(errno, name) == code, "errorcode[%d] is %s" % (code, name)

# The names the built-in module does not provide are filled in by this module.
# Codes 1 to 34 are the same on every platform MicroPython runs on.
assert errno.EPERM == 1, errno.EPERM
assert errno.ESRCH == 3, errno.ESRCH
assert errno.ENOTBLK == 15, errno.ENOTBLK
assert errno.EDOM == 33, errno.EDOM
assert errno.ERANGE == 34, errno.ERANGE
