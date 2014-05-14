import sys
sys.path[0] = "os"
from path import *

assert split("") == ("", "")
assert split("path") == ("", "path")
assert split("/") == ("/", "")
assert split("/foo") == ("/", "foo")
assert split("/foo/") == ("/foo", "")
assert split("/foo/bar") == ("/foo", "bar")

assert exists("test_path.py")
assert not exists("test_path.py--")

assert isdir("os")
assert not isdir("os--")
assert not isdir("test_path.py")
