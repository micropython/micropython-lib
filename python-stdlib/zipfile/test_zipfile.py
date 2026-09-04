import io
import sys
import unittest
import zipfile

# TODO: Find out which archiver can create ZSTD blobs
null_zip_contents = (
    ("null_bzip2.bin", 12, 4096, 46, (2026, 9, 4, 10, 1, 28), 0xC71C0011),
    ("null_deflate.bin", zipfile.ZIP_DEFLATED, 4096, 20, (2026, 9, 4, 10, 1, 32), 0xC71C0011),
    ("null_lzma.bin", 14, 4096, 41, (2026, 9, 4, 10, 1, 32), 0xC71C0011),
    ("null_stored.bin", zipfile.ZIP_STORED, 4096, 4096, (2026, 9, 4, 10, 1, 20), 0xC71C0011),
)

deflate_zip_contents = (
    ("directory/", True, 0, 0, 0, None),
    ("directory/hello_again.txt", False, 6656, 66, 0x946F8D8C, b"Hello again, MicroPython!\n"),
    ("empty", False, 0, 0, 0, None),
    ("hello.txt", False, 5120, 57, 0xA89FD9B3, b"Hello, MicroPython!\n"),
)

stored_zip_contents = (
    ("directory/", True, 0, 0, 0, None),
    ("directory/hello_again.txt", False, 6656, 6656, 0x946F8D8C, b"Hello again, MicroPython!\n"),
    ("empty", False, 0, 0, 0, None),
    ("hello.txt", False, 5120, 5120, 0xA89FD9B3, b"Hello, MicroPython!\n"),
)

TEST_NULL = "tests/null.zip"
TEST_STORED = "tests/stored.zip"
TEST_DEFLATED = "tests/deflated.zip"

class TestZipFile(unittest.TestCase):
    def check_header(self, file, expected):
        name, method, uncompressed_size, compressed_size, timestamp, crc32 = expected
        self.assertEqual(name, file.filename)
        self.assertEqual(method, file.compress_type)
        self.assertEqual(uncompressed_size, file.file_size)
        self.assertEqual(compressed_size, file.compress_size)
        self.assertEqual(timestamp, file.date_time)
        self.assertEqual(crc32, file.CRC)

    def test_null_iter(self):
        zf = zipfile.ZipFile(TEST_NULL)
        for index, info in enumerate(zf.infolist()):
            self.check_header(info, null_zip_contents[index])
        zf.close()

    def test_null_missing(self):
        with zipfile.ZipFile(TEST_NULL) as zf:
            with self.assertRaises(KeyError):
                zf.getinfo("missing.txt")

    def test_null_stored_read(self):
        zf = zipfile.ZipFile(TEST_NULL)
        expected = bytes(4096)
        for index, name in enumerate(zf.namelist()):
            self.assertEqual(name, null_zip_contents[index][0])
            if null_zip_contents[index][1] != zipfile.ZIP_STORED:
                continue
            self.assertEqual(zf.read(name), expected)
        zf.close()

    def test_null_deflated_read(self):
        if sys.implementation.name == "micropython":
            try:
                import deflate
            except ImportError:
                self.skipTest("no deflate module")
        zf = zipfile.ZipFile(TEST_NULL)
        expected = bytes(4096)
        for index, name in enumerate(zf.namelist()):
            self.assertEqual(name, null_zip_contents[index][0])
            if null_zip_contents[index][1] != zipfile.ZIP_DEFLATED:
                continue
            self.assertEqual(zf.read(name), expected)
        zf.close()

    def test_null_unsupported_read(self):
        if sys.implementation.name != "micropython":
            self.skipTest("cannot guarantee lack of methods support")
        zf = zipfile.ZipFile(TEST_NULL)
        for index, name in enumerate(zf.namelist()):
            self.assertEqual(name, null_zip_contents[index][0])
            if null_zip_contents[index][1] not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
                with self.assertRaises(NotImplementedError):
                    zf.read(name)
        zf.close()

    def test_null_stored_open(self):
        zf = zipfile.ZipFile(TEST_NULL)
        expected = bytes(4096)
        for index, name in enumerate(zf.namelist()):
            self.assertEqual(name, null_zip_contents[index][0])
            if null_zip_contents[index][1] != zipfile.ZIP_STORED:
                continue
            with zf.open(name) as f:
                self.assertEqual(expected, f.read())
        zf.close()

    def test_null_deflated_open(self):
        if sys.implementation.name == "micropython":
            try:
                import deflate
            except ImportError:
                self.skipTest("no deflate module")
        zf = zipfile.ZipFile(TEST_NULL)
        expected = bytes(4096)
        for index, name in enumerate(zf.namelist()):
            self.assertEqual(name, null_zip_contents[index][0])
            if null_zip_contents[index][1] != zipfile.ZIP_DEFLATED:
                continue
            with zf.open(name) as f:
                self.assertEqual(expected, f.read())
        zf.close()

    def test_null_unsupported_open(self):
        if sys.implementation.name != "micropython":
            self.skipTest("cannot guarantee lack of methods support")
        zf = zipfile.ZipFile(TEST_NULL)
        for index, name in enumerate(zf.namelist()):
            self.assertEqual(name, null_zip_contents[index][0])
            if null_zip_contents[index][1] not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
                with self.assertRaises(NotImplementedError):
                    with zf.open(name):
                        self.fail()
        zf.close()

    def test_null_getinfo(self):
        zf = zipfile.ZipFile(TEST_NULL)
        for zc in null_zip_contents:
            info = zf.getinfo(zc[0])
            self.check_header(info, zc)
        zf.close()

    def test_context(self):
        with zipfile.ZipFile(TEST_NULL) as zf:
            for index, info in enumerate(zf.infolist()):
                self.check_header(info, null_zip_contents[index])

    def test_close(self):
        zf = zipfile.ZipFile(TEST_NULL)
        zf.close()
        zf.close()  # check this doesn't raise

        # CPython doesn't raise as the archive directory is cached and not
        # flushed once `close` is called.  `namelist` and `infolist` do not
        # raise on CPython.
        if sys.implementation.name == "micropython":
            with self.assertRaises(ValueError):
                zf.namelist()
            with self.assertRaises(ValueError):
                zf.infolist()
        with self.assertRaises(ValueError):
            zf.open(null_zip_contents[0][0])
        with self.assertRaises(ValueError):
            with zf.open(null_zip_contents[0][0]):
                self.fail()
        with self.assertRaises(ValueError):
            zf.read(null_zip_contents[0][0])

    def check_contents(self, zf, found, expected, method):
        self.assertEqual(found.is_dir(), expected[1])
        self.assertEqual(found.file_size, expected[2])
        self.assertEqual(found.compress_size, expected[3])
        self.assertEqual(found.CRC, expected[4])
        self.assertEqual(found.compress_type, zipfile.ZIP_STORED if expected[2] == 0 else method)
        if payload := expected[5]:
            data = payload * 256
            with zf.open(expected[0]) as f:
                self.assertEqual(f.read(), data)
            self.assertEqual(zf.read(expected[0]), data)

    def test_read_deflate(self):
        if sys.implementation.name == "micropython":
            try:
                import deflate
            except ImportError:
                self.skipTest("no deflate module")
        with zipfile.ZipFile(TEST_DEFLATED) as zf:
            for file in deflate_zip_contents:
                info = zf.getinfo(file[0])
                self.check_contents(zf, info, file, zipfile.ZIP_DEFLATED)

    def test_read_stored(self):
        with zipfile.ZipFile(TEST_STORED) as zf:
            for file in stored_zip_contents:
                info = zf.getinfo(file[0])
                self.check_contents(zf, info, file, zipfile.ZIP_STORED)

    def test_is_zipfile(self):
        for n in (TEST_STORED, TEST_NULL, TEST_DEFLATED):
            self.assertEqual(zipfile.is_zipfile(n), True)
            with open(n, "rb") as f:
                old_offset = f.tell()
                self.assertEqual(zipfile.is_zipfile(f), True)
                self.assertEqual(f.tell(), old_offset)

        self.assertEqual(zipfile.is_zipfile("test_zipfile.py"), False)
        with open("test_zipfile.py", "rb") as f:
            old_offset = f.tell()
            self.assertEqual(zipfile.is_zipfile(f), False)
            self.assertEqual(f.tell(), old_offset)

        self.assertEqual(zipfile.is_zipfile("missing.zip"), False)
        self.assertEqual(zipfile.is_zipfile("zipfile"), False)

        with io.BytesIO() as empty:
            self.assertEqual(zipfile.is_zipfile(empty), False)
