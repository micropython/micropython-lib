from os.path import *

assert split("") == ("", "")
assert split("path") == ("", "path")
assert split("/") == ("/", "")
assert split("/foo") == ("/", "foo")
assert split("/foo/") == ("/foo", "")
assert split("/foo/bar") == ("/foo", "bar")
