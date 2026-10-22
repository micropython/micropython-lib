import os

_DEFAULTS = {"certs": "certifi.default", "path": "cacerts"}


def load_ca_certs(certs=None, path=None):
    global _DEFAULTS
    _ca_certs = b""
    if certs:
        _DEFAULTS["certs"] = certs

    if path:
        _DEFAULTS["path"] = path

    if _DEFAULTS["certs"]:
        if isinstance(_DEFAULTS["certs"], (bytes, bytearray)):
            return _DEFAULTS["certs"]
        try:
            cacerts = __import__(_DEFAULTS["certs"], [], [], ["default"])
            if not _DEFAULTS["path"] or _DEFAULTS["path"] not in os.listdir():
                return cacerts.CACERTS
            else:
                _ca_certs += cacerts.CACERTS
        except Exception:
            print("WARNING: No default CA certs found")

    if _DEFAULTS["path"] and _DEFAULTS["path"] in os.listdir():
        for ca_cert in os.listdir(_DEFAULTS["path"]):
            with open(f"{_DEFAULTS['path']}/{ca_cert}", "rb") as cafile:
                _ca_certs += cafile.read()

    if _ca_certs:
        return _ca_certs


def config(certs=None, path=None):
    global _DEFAULTS
    if certs is None and path is None:
        print(_DEFAULTS)
    else:
        if certs is not None:
            _DEFAULTS["certs"] = certs

        if path is not None:
            _DEFAULTS["path"] = path
