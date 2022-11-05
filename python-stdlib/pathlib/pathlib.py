import os


def _try(ok, f, *args, **kwargs):
    if ok:
        try:
            f(*args, **kwargs)
        except OSError:
            pass
    else:
        f(*args, **kwargs)


class Path:
    def __init__(self, *segments):
        self._path = "/".join(segments)
        # self._path will never end in "/"
        while self._path[-1] == "/":
            self._path = self._path[:-1]

    def __truediv__(self, other):
        return self._path + "/" + other

    def open(self, mode='r', encoding=None):
        with open(self._path, mode) as f:
            yield f

    def exists(self):
        try:
            os.stat(self._path)
        except OSError:
            return False
        return True

    def mkdir(self, parents=False, exist_ok=False):
        if parents:
            segments = self._path.split("/")
            if segments[0] == "":
                segments = segments[1:]
                progressive_path = "/"
            else:
                progressive_path = ""
            for segment in segments:
                progressive_path += "/" + segment
                _try(
                    not (progressive_path == self._path and not exist_ok),
                    os.mkdir,
                    progressive_path
                )
        else:
            _try(exist_ok, os.mkdir, self._path)

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
                yield self._glob(full_path, pattern, recursive=recursive)

    def glob(self, pattern):
        """Iterate over this subtree and yield all existing files (of any
        kind, including directories) matching the given relative pattern.

        Currently only supports a single "*" pattern.
        """
        return self._glob(self._path, pattern, recursive=False)

    def rglob(self, pattern):
        return self._glob(self._path, pattern, recursive=True)

    def stat(self):
        return os.stat(self._path)

    def read_bytes(self):
        with open(self._path, "rb") as f:
            return f.read()

    def read_text(self, encoding=None):
        with open(self._path, "r") as f:
            return f.read()

    def rename(self, target):
        os.rename(self._path, target)

    def rmdir(self):
        os.rmdir(self._path)

    def touch(self, exist_ok=True):
        try:
            os.stat(self._path)
        except OSError:
            if not exist_ok:
                return

        with open(self._path):
            pass

    def unlink(self, missing_ok=False):
        _try(missing_ok, os.unlink, self._path)

    def write_bytes(self, data):
        with open(self._path, "wb") as f:
            f.write(data)

    def write_text(self, data, encoding=None):
        with open(self._path, "w") as f:
            f.write(data)

    @property
    def stem(self):
        return self.name.rsplit(".", 1)[0]

    @property
    def parent(self):
        return Path(*self._path.split("/"))

    @property
    def name(self):
        return self._path.rsplit("/", 1)[-1]

    @property
    def suffix(self):
        elems = self._path.rsplit(".", 1)
        if len(elems) == 1:
            return ""
        else:
            return "." + elems[-1]
