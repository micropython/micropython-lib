import errno
import os
import random
import shutil

_ascii_letters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


def _get_candidate_name(size=8):
    return "".join(random.choice(_ascii_letters) for _ in range(size))


def _sanitize_inputs(suffix, prefix, dir):
    if dir is None:
        dir = "/tmp"
    if suffix is None:
        suffix = ""
    if prefix is None:
        prefix = ""
    return suffix, prefix, dir


def _try(action, *args, **kwargs):
    try:
        action(*args, **kwargs)
        return True
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise e
    return False


def mkdtemp(suffix=None, prefix=None, dir=None):
    suffix, prefix, dir = _sanitize_inputs(suffix, prefix, dir)

    _try(os.mkdir, dir)

    while True:
        name = _get_candidate_name()
        file = dir + "/" + prefix + name + suffix
        if _try(os.mkdir, file):
            return file


class TemporaryDirectory:
    def __init__(self, suffix=None, prefix=None, dir=None):
        self.name = mkdtemp(suffix, prefix, dir)

    def __repr__(self):
        return "<{} {!r}>".format(self.__class__.__name__, self.name)

    def __enter__(self):
        return self.name

    def __exit__(self, exc, value, tb):
        self.cleanup()

    def cleanup(self):
        _try(shutil.rmtree, self.name)
