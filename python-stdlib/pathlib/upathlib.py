import errno
import os


def _absolute(path):
    cwd = os.getcwd()
    if not path or path == ".":
        return cwd
    if path[0] == "/":
        return path
    path = path.rstrip("/")
    return "/" + path if cwd == "/" else cwd + "/" + path


class Path:
    def __init__(self, *segments):
        segments_stripped = []
        for segment in segments:
            if not segment:
                segment = "."
            if not segments_stripped and segment[0] == "/":
                segments_stripped.append("")
            while segment[-1] == "/":
                segment = segment[:-1]
            while segment[0] == "/":
                segment = segment[1:]
            segments_stripped.append(segment)

        self._abs_path = _absolute("/".join(segments_stripped))

    def __truediv__(self, other):
        return self._abs_path + "/" + other

    def __repr__(self):
        return f"{type(self).__name__}(\"{self._abs_path}\")"

    def __str__(self):
        return self._abs_path

    def __eq__(self, other):
        return self._abs_path == str(other)


    def open(self, mode='r', encoding=None):
        return open(self._abs_path, mode, encoding=encoding)

    def exists(self):
        try:
            os.stat(self._abs_path)
        except OSError:
            return False
        return True

    def mkdir(self, parents=False, exist_ok=False):
        try:
            os.mkdir(self._abs_path)
        except OSError as e:
            if e.errno == errno.EEXIST:
                if exist_ok:
                    return
                else:
                    raise e
            elif e.errno == errno.ENOENT:
                if parents:
                    # handled below
                    pass
                else:
                    raise e
            else:
                raise e

        segments = self._abs_path.split("/")
        if segments[0] == "":
            segments = segments[1:]
            progressive_path = "/"
        else:
            progressive_path = ""
        for segment in segments:
            progressive_path += "/" + segment

            try:
                os.mkdir(progressive_path)
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise e

    def is_dir(self):
        try:
            if self.stat()[0] & 0x4000:
                return True
        except OSError:
            pass
        return False

    def is_file(self):
        try:
            if self.stat()[0] & 0x8000:
                return True
        except OSError:
            pass
        return False

    def _glob(self, path, pattern, recursive):
        # Currently only supports a single "*" pattern.
        n_wildcards = pattern.count("*")
        n_single_wildcards = pattern.count("?")

        if n_single_wildcards:
            raise NotImplementedError("? single wildcards not implemented.")

        if n_wildcards == 0:
            raise ValueError
        elif n_wildcards > 1:
            raise NotImplementedError("Multiple * wildcards not implemented.")

        prefix, suffix = pattern.split("*")

        for elem in os.ilistdir(path):
            name = elem[0]
            full_path = path + "/" + name
            if name.startswith(prefix) and name.endswith(suffix):
                yield full_path
            if elem[1] & 0x4000 and recursive:  # is_dir
                yield from self._glob(full_path, pattern, recursive=recursive)

    def glob(self, pattern):
        """Iterate over this subtree and yield all existing files (of any
        kind, including directories) matching the given relative pattern.

        Currently only supports a single "*" pattern.
        """
        return self._glob(self._abs_path, pattern, recursive=False)

    def rglob(self, pattern):
        return self._glob(self._abs_path, pattern, recursive=True)

    def stat(self):
        return os.stat(self._abs_path)

    def read_bytes(self):
        with open(self._abs_path, "rb") as f:
            return f.read()

    def read_text(self, encoding=None):
        with open(self._abs_path, "r") as f:
            return f.read()

    def rename(self, target):
        os.rename(self._abs_path, target)

    def rmdir(self):
        os.rmdir(self._abs_path)

    def touch(self, exist_ok=True):
        try:
            os.stat(self._abs_path)
        except OSError as e:
            if e.errno == errno.ENOENT:
                with open(self._abs_path, "w"):
                    pass
            else:
                raise e

    def unlink(self, missing_ok=False):
        try:
            os.unlink(self._abs_path)
        except OSError as e:
            if not missing_ok:
                raise e

    def write_bytes(self, data):
        with open(self._abs_path, "wb") as f:
            f.write(data)

    def write_text(self, data, encoding=None):
        with open(self._abs_path, "w") as f:
            f.write(data)

    def with_suffix(self, suffix):
        old_suffix = self.suffix
        if old_suffix:
            return Path(self._abs_path[:-len(old_suffix)] + suffix)
        else:
            return Path(self._abs_path + suffix)

    @property
    def stem(self):
        return self.name.rsplit(".", 1)[0]

    @property
    def parent(self):
        return Path(self._abs_path.rsplit("/", 1)[0])

    @property
    def name(self):
        return self._abs_path.rsplit("/", 1)[-1]

    @property
    def suffix(self):
        elems = self._abs_path.rsplit(".", 1)
        if len(elems) == 1:
            return ""
        else:
            return "." + elems[-1]
