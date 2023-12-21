import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


def _isgenerator(x):
    return isinstance(x, type((lambda: (yield))()))


class TestPathlib(unittest.TestCase):
    def assertExists(self, fn):
        os.stat(fn)

    def assertNotExists(self, fn):
        with self.assertRaises(OSError):
            os.stat(fn)

    def setUp(self):
        self._tmp_path_obj = TemporaryDirectory()
        self.tmp_path = self._tmp_path_obj.name

    def tearDown(self):
        self._tmp_path_obj.cleanup()

    def test_init_single_segment(self):
        path = Path("foo")
        self.assertTrue(path._path == "foo")

        path = Path("foo/")
        self.assertTrue(path._path == "foo")

        path = Path("/foo")
        self.assertTrue(path._path == "/foo")

        path = Path("/////foo")
        self.assertTrue(path._path == "/foo")

        path = Path("")
        self.assertTrue(path._path == ".")

    def test_init_multiple_segment(self):
        path = Path("foo", "bar")
        self.assertTrue(path._path == "foo/bar")

        path = Path("foo/", "bar")
        self.assertTrue(path._path == "foo/bar")

        path = Path("/foo", "bar")
        self.assertTrue(path._path == "/foo/bar")

        path = Path("/foo", "", "bar")
        self.assertTrue(path._path == "/foo/bar")

        path = Path("/foo/", "", "/bar/")
        self.assertTrue(path._path == "/bar")

        path = Path("", "")
        self.assertTrue(path._path == ".")

    def test_truediv_join_str(self):
        actual = Path("foo") / "bar"
        self.assertTrue(actual == Path("foo/bar"))

    def test_truediv_join_path(self):
        actual = Path("foo") / Path("bar")
        self.assertTrue(actual == Path("foo/bar"))

        actual = Path("foo") / Path("/bar")
        self.assertTrue(actual == "/bar")

    def test_eq_and_absolute(self):
        self.assertTrue(Path("") == Path("."))
        self.assertTrue(Path("foo") == Path(os.getcwd(), "foo"))
        self.assertTrue(Path("foo") == "foo")
        self.assertTrue(Path("foo") == os.getcwd() + "/foo")

        self.assertTrue(Path("foo") != Path("bar"))
        self.assertTrue(Path(".") != Path("/"))

    def test_open(self):
        fn = self.tmp_path + "/foo.txt"
        path = Path(fn)

        with open(fn, "w") as f:
            f.write("file contents")

        with path.open("r") as f:
            actual = f.read()

        self.assertTrue(actual == "file contents")

    def test_exists(self):
        fn = self.tmp_path + "/foo.txt"

        path = Path(str(fn))
        self.assertTrue(not path.exists())

        with open(fn, "w"):
            pass

        self.assertTrue(path.exists())

    def test_mkdir(self):
        target = self.tmp_path + "/foo/bar/baz"
        path = Path(target)

        with self.assertRaises(OSError):
            path.mkdir()

        with self.assertRaises(OSError):
            path.mkdir(exist_ok=True)

        path.mkdir(parents=True)
        self.assertExists(target)

        with self.assertRaises(OSError):
            path.mkdir(exist_ok=False)

        path.mkdir(exist_ok=True)

    def test_is_dir(self):
        target = self.tmp_path
        path = Path(target)
        self.assertTrue(path.is_dir())

        target = self.tmp_path + "/foo"
        path = Path(target)
        self.assertTrue(not path.is_dir())
        os.mkdir(target)
        self.assertTrue(path.is_dir())

        target = self.tmp_path + "/bar.txt"
        path = Path(target)
        self.assertTrue(not path.is_dir())
        with open(target, "w"):
            pass
        self.assertTrue(not path.is_dir())

    def test_is_file(self):
        target = self.tmp_path
        path = Path(target)
        self.assertTrue(not path.is_file())

        target = self.tmp_path + "/bar.txt"
        path = Path(target)
        self.assertTrue(not path.is_file())
        with open(target, "w"):
            pass
        self.assertTrue(path.is_file())

    def test_glob(self):
        foo_txt = self.tmp_path + "/foo.txt"
        with open(foo_txt, "w"):
            pass
        bar_txt = self.tmp_path + "/bar.txt"
        with open(bar_txt, "w"):
            pass
        baz_bin = self.tmp_path + "/baz.bin"
        with open(baz_bin, "w"):
            pass

        path = Path(self.tmp_path)
        glob_gen = path.glob("*.txt")
        self.assertTrue(_isgenerator(glob_gen))

        res = [str(x) for x in glob_gen]
        self.assertTrue(len(res) == 2)
        self.assertTrue(foo_txt in res)
        self.assertTrue(bar_txt in res)

    def test_rglob(self):
        foo_txt = self.tmp_path + "/foo.txt"
        with open(foo_txt, "w"):
            pass
        bar_txt = self.tmp_path + "/bar.txt"
        with open(bar_txt, "w"):
            pass
        baz_bin = self.tmp_path + "/baz.bin"
        with open(baz_bin, "w"):
            pass

        boop_folder = self.tmp_path + "/boop"
        os.mkdir(boop_folder)
        bap_txt = self.tmp_path + "/boop/bap.txt"
        with open(bap_txt, "w"):
            pass

        path = Path(self.tmp_path)
        glob_gen = path.rglob("*.txt")
        self.assertTrue(_isgenerator(glob_gen))

        res = [str(x) for x in glob_gen]
        self.assertTrue(len(res) == 3)
        self.assertTrue(foo_txt in res)
        self.assertTrue(bar_txt in res)
        self.assertTrue(bap_txt in res)

    def test_stat(self):
        expected = os.stat(self.tmp_path)
        path = Path(self.tmp_path)
        actual = path.stat()
        self.assertTrue(expected == actual)

    def test_rmdir(self):
        target = self.tmp_path + "/foo"
        path = Path(target)

        with self.assertRaises(OSError):
            # Doesn't exist
            path.rmdir()

        os.mkdir(target)
        self.assertExists(target)
        path.rmdir()
        self.assertNotExists(target)

        os.mkdir(target)
        with open(target + "/bar.txt", "w"):
            pass

        with self.assertRaises(OSError):
            # Cannot rmdir; contains file.
            path.rmdir()

    def test_touch(self):
        target = self.tmp_path + "/foo.txt"

        path = Path(target)
        path.touch()
        self.assertExists(target)

        path.touch()  # touching existing file is fine
        self.assertExists(target)

        # Technically should be FileExistsError,
        # but thats not builtin to micropython
        with self.assertRaises(OSError):
            path.touch(exist_ok=False)

        path = Path(self.tmp_path + "/bar/baz.txt")
        with self.assertRaises(OSError):
            # Parent directory does not exist
            path.touch()

    def test_unlink(self):
        target = self.tmp_path + "/foo.txt"

        path = Path(target)
        with self.assertRaises(OSError):
            # File does not exist
            path.unlink()

        with open(target, "w"):
            pass

        self.assertExists(target)
        path.unlink()
        self.assertNotExists(target)

        path = Path(self.tmp_path)
        with self.assertRaises(OSError):
            # File does not exist
            path.unlink()

    def test_write_bytes(self):
        target = self.tmp_path + "/foo.bin"
        path = Path(target)
        path.write_bytes(b"test byte data")
        with open(target, "rb") as f:
            actual = f.read()
        self.assertTrue(actual == b"test byte data")

    def test_write_text(self):
        target = self.tmp_path + "/foo.txt"
        path = Path(target)
        path.write_text("test string")
        with open(target, "r") as f:
            actual = f.read()
        self.assertTrue(actual == "test string")

    def test_read_bytes(self):
        target = self.tmp_path + "/foo.bin"
        with open(target, "wb") as f:
            f.write(b"test byte data")

        path = Path(target)
        actual = path.read_bytes()
        self.assertTrue(actual == b"test byte data")

    def test_read_text(self):
        target = self.tmp_path + "/foo.bin"
        with open(target, "w") as f:
            f.write("test string")

        path = Path(target)
        actual = path.read_text()
        self.assertTrue(actual == "test string")

    def test_stem(self):
        self.assertTrue(Path("foo/test").stem == "test")
        self.assertTrue(Path("foo/bar.bin").stem == "bar")
        self.assertTrue(Path("").stem == "")

    def test_name(self):
        self.assertTrue(Path("foo/test").name == "test")
        self.assertTrue(Path("foo/bar.bin").name == "bar.bin")

    def test_parent(self):
        self.assertTrue(Path("foo/test").parent == Path("foo"))
        self.assertTrue(Path("foo/bar.bin").parent == Path("foo"))
        self.assertTrue(Path("bar.bin").parent == Path("."))
        self.assertTrue(Path(".").parent == Path("."))
        self.assertTrue(Path("/").parent == Path("/"))

    def test_suffix(self):
        self.assertTrue(Path("foo/test").suffix == "")
        self.assertTrue(Path("foo/bar.bin").suffix == ".bin")
        self.assertTrue(Path("bar.txt").suffix == ".txt")

    def test_with_suffix(self):
        self.assertTrue(Path("foo/test").with_suffix(".tar") == Path("foo/test.tar"))
        self.assertTrue(Path("foo/bar.bin").with_suffix(".txt") == Path("foo/bar.txt"))
        self.assertTrue(Path("bar.txt").with_suffix("") == Path("bar"))

    def test_rtruediv(self):
        """Works as of micropython ea7031f"""
        res = "foo" / Path("bar")
        self.assertTrue(res == Path("foo/bar"))

    def test_rtruediv_inplace(self):
        """Works as of micropython ea7031f"""
        res = "foo"
        res /= Path("bar")
        self.assertTrue(res == Path("foo/bar"))
