import os


# Read the output of a process.
f = os.popen("echo hello")
assert f.read() == "hello\n"
assert f.close() is None

# Read the output line by line.
f = os.popen("printf 'a\nb\n'")
assert f.readline() == "a\n"
assert list(f) == ["b\n"]
assert f.close() is None

# Use the stream as a context manager.
with os.popen("echo hello") as f:
    assert f.read() == "hello\n"

# Write to the input of a process.
with os.popen("cat > test_popen.tmp", "w") as f:
    f.write("hello\n")
with open("test_popen.tmp") as f:
    assert f.read() == "hello\n"
os.unlink("test_popen.tmp")

# A non-zero exit status is reported by close(), the same way CPython does it.
f = os.popen("exit 3")
f.read()
assert f.close() == 3 << 8

# Closing twice is allowed and reports the same status.
f = os.popen("exit 3")
f.read()
assert f.close() == 3 << 8
assert f.close() == 3 << 8

# The child is reaped by close(), it does not stay around as a zombie, and
# both ends of the pipe are closed, so no file descriptors are leaked either.
children = "/proc/self/task/%d/children" % os.getpid()
if os.access(children, os.F_OK):
    fds = len(os.listdir("/proc/self/fd"))
    for _ in range(50):
        f = os.popen("echo hello")
        assert f.read() == "hello\n"
        assert f.close() is None
    for _ in range(50):
        with os.popen("cat > /dev/null", "w") as f:
            f.write("hello\n")
    with open(children) as f:
        assert f.read().split() == []
    assert len(os.listdir("/proc/self/fd")) == fds
