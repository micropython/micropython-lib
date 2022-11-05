import os
from importlib.machinery import SourceFileLoader

import pytest

from upathlib import Path


def ilistdir(x):
    for name in os.listdir(x):
        stat = os.stat(x + "/" + name)  # noqa: PL116
        yield (name, stat.st_mode, stat.st_ino)


os.ilistdir = ilistdir

@pytest.fixture
def tmp_path_str_str(tmp_path_str):
    return tmp_path_str_str


def test_init_single_segment():
    path = Path("foo")
    assert path._path == "foo"

    path = Path("foo/")
    assert path._path == "foo"

    path = Path("/foo")
    assert path._path == "/foo"


def test_init_multiple_segment():
    path = Path("foo", "bar")
    assert path._path == "foo/bar"

    path = Path("foo/", "bar")
    assert path._path == "foo/bar"

    path = Path("/foo", "bar")
    assert path._path == "/foo/bar"


def test_truediv_join():
    pass


def test_open():
    pass


def test_exists(tmp_path_str):
    pass


def test_mkdir(tmp_path_str):
    pass


def test_glob(tmp_path_strl):
    pass


def test_rglob(tmp_path_str):
    pass


def test_stat(tmp_path_str):
    pass


def test_rmdir(tmp_path_str):
    pass


def test_touch(tmp_path_str):
    pass

def test_unlink(tmp_path_str):
    pass

def test_write_bytes(tmp_path_str):
    pass

def test_write_text(tmp_path_str):
    pass

def test_read_bytes(tmp_path_str):
    pass

def test_read_text(tmp_path_str):
    pass

def test_stem():
    pass

def test_name():
    pass

def test_parent():
    pass

def test_suffix():
    pass
