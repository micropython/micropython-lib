# MicroPython package installer
# MIT license; Copyright (c) 2022 Jim Mussared
# Modified by Ned Konz to allow relative source URLs in package.json files

import urequests as requests
import sys
import gc  # TODO: remove
import network

_PACKAGE_INDEX = const("https://micropython.org/pi/v2")
_CHUNK_SIZE = 128
_URL_PREFIXES = const(("http://", "https://", "github:", "file://"))

_top_url = ""
_wlan = None


# Return true if name is a URI that we understand
def _is_url(name):
    return any(name.startswith(prefix) for prefix in _URL_PREFIXES)


# This implements os.makedirs(os.dirname(path))
def _ensure_path_exists(path):
    import os

    split = path.split("/")

    # Handle paths starting with "/".
    if not split[0]:
        split.pop(0)
        split[0] = "/" + split[0]

    prefix = ""
    for i in range(len(split) - 1):
        prefix += split[i]
        try:
            os.stat(prefix)
        except:
            os.mkdir(prefix)
        prefix += "/"


# Copy from src (stream) to dest (function-taking-bytes)
def _chunk(src, dest):
    buf = memoryview(bytearray(_CHUNK_SIZE))
    while True:
        n = src.readinto(buf)
        if n == 0:
            break
        dest(buf if n == _CHUNK_SIZE else buf[:n])


# Check if the specified path exists and matches the hash.
def _check_exists(path, short_hash):
    try:
        import binascii
        import hashlib

        with open(path, "rb") as f:
            hs256 = hashlib.sha256()
            _chunk(f, hs256.update)
            existing_hash = str(binascii.hexlify(hs256.digest())[: len(short_hash)], "utf-8")
            return existing_hash == short_hash
    except:
        return False


def _rewrite_github_url(url, branch):
    url = url[7:].split("/")  # user, repo, path...
    url = "/".join(
        (
            "https://raw.githubusercontent.com",
            url[0],  # user
            url[1],  # repo
            branch,
            "/".join(url[2:]),
        )
    )
    return url


def _rewrite_url(orig_url, branch=None):
    global _top_url  # the origin of the package.json URL for re-writing relative URLs

    print(f"Rewriting {orig_url} with branch {branch} from {_top_url} to ", end="")  # TODO remove

    # rewrite relative URLs as absolute URLs
    if not _is_url(orig_url):
        orig_url = _top_url + "/" + orig_url

    url = orig_url

    # now rewrite github: URLs as raw.githubusercontent.com URLs
    if orig_url.startswith("github:"):
        if not branch:
            branch = "HEAD"
        url = _rewrite_github_url(orig_url, branch)

        # catch URLs that don't start with the same github:user/repo
        if not url.startswith(_top_url):
            url = _rewrite_github_url(orig_url, "HEAD")

    print(url)  # TODO remove
    return url


def _check_network():
    global _wlan
    if not _wlan:
        _wlan = network.WLAN(network.STA_IF)
    if not _wlan.isconnected():
        print("waiting for network...")
        while not _wlan.isconnected():
            pass


def _download_file(url, dest):
    # if url is a file:// url, just copy it
    if url.startswith("file://"):
        src_name = url[7:]
        try:
            with open(src_name, "rb") as src:
                print(f"Copying file {src_name} to {dest}")
                _ensure_path_exists(dest)
                with open(dest, "wb") as dst:
                    _chunk(src, dst.write)
            return True
        except OSError:
            print(f"File {src_name} not found")
            return False

    retries = 0
    while retries < 5:
        gc.collect()
        print(f"Free memory: {gc.mem_free()}")  # TODO: remove
        try:
            response = requests.get(url)

            if response.status_code != 200:
                print("Error", response.status_code, "requesting", url)
                return False

            print("Copying:", dest)
            _ensure_path_exists(dest)
            with open(dest, "wb") as f:
                _chunk(response.raw, f.write)

            return True
        except OSError as e:
            print(f"after exc {e}: Free memory: {gc.mem_free()}; waiting")  # TODO: remove
            retries += 1
            time.sleep(1)
            response.close()
            continue

        finally:
            response.close()


def _install_json(package_json_url, index, target, version, mpy):
    global _top_url
    # if package_json_url is a file:// url, just download it
    # and use its json directly
    if package_json_url.startswith("file://"):
        import ujson as json

        pkg_name = package_json_url[7:]
        try:
            with open(pkg_name) as json_file:
                package_json = json.load(json_file)
        except OSError:
            print(f"File {pkg_name} not found")
            return False
    else:
        pkg_name = _rewrite_url(package_json_url, version)
        response = requests.get(pkg_name)
        try:
            if response.status_code != 200:
                print(f"Package {package_json_url} not found (tried {pkg_name})")
                return False

            package_json = response.json()
        finally:
            response.close()
    _top_url = pkg_name.rsplit("/", 1)[0]

    # get mpy files from hashes
    for target_path, short_hash in package_json.get("hashes", ()):
        fs_target_path = target + "/" + target_path
        if _check_exists(fs_target_path, short_hash):
            print("Exists:", fs_target_path)
        else:
            file_url = "{}/file/{}/{}".format(index, short_hash[:2], short_hash)
            if not _download_file(file_url, fs_target_path):
                print("File not found: {} {}".format(target_path, short_hash))
                return False
    # get other files from URLs
    for target_path, url in package_json.get("urls", ()):
        fs_target_path = target + "/" + target_path
        if not _download_file(_rewrite_url(url, version), fs_target_path):
            print("File not found: {} {}".format(target_path, url))
            return False
    # install dependencies
    for dep, dep_version in package_json.get("deps", ()):
        if not _install_package(dep, index, target, dep_version, mpy):
            return False
    return True


def _install_package(package, index, target, version, mpy):
    if _is_url(package):
        if package.endswith(".py") or package.endswith(".mpy"):
            print("Downloading {} to {}".format(package, target))
            return _download_file(
                _rewrite_url(package, version), target + "/" + package.rsplit("/")[-1]
            )
        else:
            if not package.endswith(".json"):
                if not package.endswith("/"):
                    package += "/"
                package += "package.json"
            print("Installing {} to {}".format(package, target))
    else:
        if not version:
            version = "latest"
        print("Installing {} ({}) from {} to {}".format(package, version, index, target))

        mpy_version = (
            sys.implementation._mpy & 0xFF if mpy and hasattr(sys.implementation, "_mpy") else "py"
        )

        package = "{}/package/{}/{}/{}.json".format(index, mpy_version, package, version)

    return _install_json(package, index, target, version, mpy)


def install(package, index=None, target=None, version=None, mpy=True):
    if not target:
        for p in sys.path:
            if p.endswith("/lib"):
                target = p
                break
        else:
            print("Unable to find lib dir in sys.path")
            return

    if not index:
        index = _PACKAGE_INDEX

    if _install_package(package, index.rstrip("/"), target, version, mpy):
        print("Done")
    else:
        print("Package may be partially installed")
