import inspect
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
def mock_os_getcwd(mocker):
    return mocker.patch("upathlib.os.getcwd", return_value="/")


def test_init_single_segment(mock_os_getcwd):
    path = Path("foo")
    assert path._abs_path == "/foo"

    path = Path("foo/")
    assert path._abs_path == "/foo"

    path = Path("/foo")
    assert path._abs_path == "/foo"


def test_init_multiple_segment(mock_os_getcwd):
    path = Path("foo", "bar")
    assert path._abs_path == "/foo/bar"

    path = Path("foo/", "bar")
    assert path._abs_path == "/foo/bar"

    path = Path("/foo", "bar")
    assert path._abs_path == "/foo/bar"


def test_truediv_join():
    pass


def test_open(tmp_path):
    fn = tmp_path / "foo.txt"
    path = Path(str(fn))

    with path.open("w") as f:
        f.write("file contents")

    with path.open("r") as f:
        actual = f.read()

    assert actual == "file contents"


def test_exists(tmp_path):
    fn = tmp_path / "foo.txt"

    path = Path(str(fn))
    assert not path.exists()

    fn.touch()

    assert path.exists()


def test_mkdir(tmp_path):
    target = tmp_path / "foo" / "bar" / "baz"
    path = Path(str(target))

    with pytest.raises(OSError):
        path.mkdir()

    with pytest.raises(OSError):
        path.mkdir(exist_ok=True)

    path.mkdir(parents=True)
    assert target.is_dir()

    with pytest.raises(OSError):
        path.mkdir(exist_ok=False)

    path.mkdir(exist_ok=True)


def test_is_dir(tmp_path):
    target = tmp_path
    path = Path(str(target))
    assert path.is_dir()

    target = tmp_path / "foo"
    path = Path(str(target))
    assert not path.is_dir()
    target.mkdir()
    assert path.is_dir()

    target = tmp_path / "bar.txt"
    path = Path(str(target))
    assert not path.is_dir()
    target.touch()
    assert not path.is_dir()


def test_is_file(tmp_path):
    target = tmp_path
    path = Path(str(target))
    assert not path.is_file()

    target = tmp_path / "bar.txt"
    path = Path(str(target))
    assert not path.is_file()
    target.touch()
    assert path.is_file()


def test_glob(tmp_path):
    foo_txt = tmp_path / "foo.txt"
    foo_txt.touch()
    bar_txt = tmp_path / "bar.txt"
    bar_txt.touch()
    baz_bin = tmp_path / "baz.bin"
    baz_bin.touch()

    path = Path(str(tmp_path))
    res = path.glob("*.txt")
    assert inspect.isgenerator(res)

    res = [str(x) for x in res]
    assert len(res) == 2
    assert str(foo_txt) in res
    assert str(bar_txt) in res


def test_rglob(tmp_path):
    foo_txt = tmp_path / "foo.txt"
    foo_txt.touch()
    bar_txt = tmp_path / "bar.txt"
    bar_txt.touch()
    baz_bin = tmp_path / "baz.bin"
    baz_bin.touch()
    boop_folder = tmp_path / "boop"
    boop_folder.mkdir()
    bap_txt = tmp_path / "boop" / "bap.txt"
    bap_txt.touch()

    path = Path(str(tmp_path))
    res = path.rglob("*.txt")
    assert inspect.isgenerator(res)

    res = [str(x) for x in res]
    assert len(res) == 3
    assert str(foo_txt) in res
    assert str(bar_txt) in res
    assert str(bap_txt) in res


def test_stat(tmp_path):
    expected = os.stat(tmp_path)
    path = Path(str(tmp_path))
    actual = path.stat()
    assert expected == actual


def test_rmdir(tmp_path):
    target = tmp_path / "foo"

    path = Path(str(target))

    with pytest.raises(OSError):
        # Doesn't exist
        path.rmdir()

    target.mkdir()
    assert target.exists()
    path.rmdir()
    assert not target.exists()

    target.mkdir()
    (target / "bar.txt").touch()
    with pytest.raises(OSError):
        # Cannot rmdir; contains file.
        path.rmdir()


def test_touch(tmp_path):
    target = tmp_path / "foo.txt"
    assert not target.exists()

    path = Path(str(target))
    path.touch()
    assert target.exists()

    path = Path(str(tmp_path / "bar" / "baz.txt"))
    with pytest.raises(OSError):
        # Parent directory does not exist
        path.touch()


def test_unlink(tmp_path):
    target = tmp_path / "foo.txt"

    path = Path(str(target))
    with pytest.raises(OSError):
        # File does not exist
        path.unlink()

    target.touch()
    assert target.exists()
    path.unlink()
    assert not target.exists()

    path = Path(str(tmp_path))
    with pytest.raises(OSError):
        # File does not exist
        path.unlink()


def test_write_bytes(tmp_path):
    target = tmp_path / "foo.bin"
    path = Path(str(target))
    path.write_bytes(b"test byte data")
    actual = target.read_bytes()
    assert actual == b"test byte data"


def test_write_text(tmp_path):
    target = tmp_path / "foo.txt"
    path = Path(str(target))
    path.write_text("test string")
    actual = target.read_text()
    assert actual == "test string"


def test_read_bytes(tmp_path):
    target = tmp_path / "foo.bin"
    target.write_bytes(b"test byte data")

    path = Path(str(target))
    actual = path.read_bytes()
    assert actual == b"test byte data"


def test_read_text(tmp_path):
    target = tmp_path / "foo.txt"
    target.write_text("test string")

    path = Path(str(target))
    actual = path.read_text()
    assert actual == "test string"


def test_stem(mock_os_getcwd):
    assert Path("foo/test").stem == "test"
    assert Path("foo/bar.bin").stem == "bar"
    assert Path("").stem == ""


def test_name():
    assert Path("foo/test").name == "test"
    assert Path("foo/bar.bin").name == "bar.bin"


def test_parent():
    assert Path("foo/test").parent == Path("foo")
    assert Path("foo/bar.bin").parent == Path("foo")
    assert Path("bar.bin").parent == Path(".")


def test_suffix():
    assert Path("foo/test").suffix == ""
    assert Path("foo/bar.bin").suffix == ".bin"
    assert Path("bar.txt").suffix == ".txt"


def test_with_suffix():
    assert Path("foo/test").with_suffix(".tar") == Path("foo/test.tar")
    assert Path("foo/bar.bin").with_suffix(".txt") == Path("foo/bar.txt")
    assert Path("bar.txt").with_suffix("") == Path("bar")
