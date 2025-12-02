import tarfile
import unittest


test_tar_contents = (
    ("a", "file", 2),
    ("b", "file", 2),
    ("dir/", "dir", 0),
    ("dir/c", "file", 2),
    ("dir/d", "file", 2),
    ("tar.tar", "file", 10240),
)

test_sub_tar_contents = (
    ("e", "file", 2),
    ("f", "file", 2),
)


class TestTarFile(unittest.TestCase):
    def check_contents(self, expected, tf):
        for i, file in enumerate(tf):
            name, type, size = expected[i]
            self.assertEqual(file.name, name)
            self.assertEqual(file.type, type)
            self.assertEqual(file.size, size)

    def test_iter(self):
        tf = tarfile.TarFile("test.tar")
        for _ in range(6):
            self.assertIsInstance(next(tf), tarfile.TarInfo)
        with self.assertRaises(StopIteration):
            next(tf)

    def test_contents(self):
        tf = tarfile.TarFile("test.tar")
        self.check_contents(test_tar_contents, tf)

    def test_nested_tar(self):
        tf = tarfile.TarFile("test.tar")
        for file in tf:
            if file.name == "tar.tar":
                subf = tf.extractfile(file)
                subtf = tarfile.TarFile(fileobj=subf)
                self.check_contents(test_sub_tar_contents, subtf)
