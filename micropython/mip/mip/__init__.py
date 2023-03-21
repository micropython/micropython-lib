# MicroPython package installer
# MIT license
# Copyright (c) 2022 Jim Mussared
# Extended with PyPI support by brainelectronics 2023

import urequests as requests
import sys


_PACKAGE_INDEX = const("https://micropython.org/pi/v2")
_CHUNK_SIZE = 128


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


def _rewrite_url(url, branch=None):
    if not branch:
        branch = "HEAD"
    if url.startswith("github:"):
        url = url[7:].split("/")
        url = (
            "https://raw.githubusercontent.com/"
            + url[0]
            + "/"
            + url[1]
            + "/"
            + branch
            + "/"
            + "/".join(url[2:])
        )
    return url


def _download_file(url, dest):
    response = requests.get(url)
    try:
        if response.status_code != 200:
            print("Error", response.status_code, "requesting", url)
            return False

        print("Copying:", dest)
        _ensure_path_exists(dest)
        with open(dest, "wb") as f:
            _chunk(response.raw, f.write)

        return True
    finally:
        response.close()


def _get_package_json(package_json_url, version):
    package_json = {}
    response = requests.get(_rewrite_url(package_json_url, version))
    try:
        if response.status_code != 200:
            print("Package not found:", package_json_url)
            return package_json

        package_json = response.json()
    finally:
        response.close()

    return package_json


def _install_json(package_json_url, index, target, version, mpy):
    package_json = _get_package_json(package_json_url, version)

    for target_path, short_hash in package_json.get("hashes", ()):
        fs_target_path = target + "/" + target_path
        if _check_exists(fs_target_path, short_hash):
            print("Exists:", fs_target_path)
        else:
            file_url = "{}/file/{}/{}".format(index, short_hash[:2], short_hash)
            if not _download_file(file_url, fs_target_path):
                print("File not found: {} {}".format(target_path, short_hash))
                return False
    for target_path, url in package_json.get("urls", ()):
        fs_target_path = target + "/" + target_path
        if not _download_file(_rewrite_url(url, version), fs_target_path):
            print("File not found: {} {}".format(target_path, url))
            return False
    for dep, dep_version in package_json.get("deps", ()):
        if not _install_package(dep, index, target, dep_version, mpy):
            return False
    return True


def _install_tar(package_json_url, index, target, version):
    import gc

    package_json = _get_package_json(package_json_url, version)
    meta = {}

    if not version:
        version = package_json.get("info", {}).get("version", "")

    if version not in package_json.get("releases", ()):
        print("Version {} not found".format(version))
        return False

    package_url = package_json["releases"][version][0]["url"]
    # save some memory, the large dict is no longer required
    del package_json
    gc.collect()

    fs_target_path = target + "/" + package_url.rsplit("/", 1)[1]

    if not _download_file(package_url, fs_target_path):
        print("Failed to download {} to {}".format(package_url, fs_target_path))
        return False

    try:
        from uzlib import DecompIO
        from utarfile import TarFile

        gzdict_sz = 16 + 15
        sz = gc.mem_free() + gc.mem_alloc()
        if sz <= 65536:
            gzdict_sz = 16 + 12

        zipped_file = open(fs_target_path, "rb")
        decompressed_file = DecompIO(zipped_file, gzdict_sz)
        tar_file = TarFile(fileobj=decompressed_file)

        meta = _install_tar_file(tar_file, target)

        zipped_file.close()
        del zipped_file
        del decompressed_file
        del tar_file
    except Exception as e:
        print("Failed to decompress downloaded file due to {}".format(e))
        return False

    # cleanup downloaded file
    try:
        from os import unlink

        unlink(fs_target_path)
    except Exception as e:
        print("Error during cleanup of {}".format(fs_target_path), e)

    gc.collect()

    deps = meta.get("deps", "").rstrip()
    if deps:
        deps = deps.decode("utf-8").split("\n")
        print("Install additional deps: {}".format(deps))
        results = []

        for ele in deps:
            res = _install_package(
                package=ele, index=index, target=target, version=None, mpy=False, pypi=True
            )
            if not res:
                print("Package may be partially installed")
            results.append(res)

        return all(results)

    return True


def _install_tar_file(f, target):
    from utarfile import DIRTYPE
    from shutil import copyfileobj

    meta = {}

    for info in f:
        if "PaxHeader" in info.name:
            continue

        print("Processing: {}".format(info))
        fname = info.name
        try:
            fname = fname[fname.index("/") + 1 :]
        except ValueError:
            fname = ""

        save = True
        for p in ("setup.", "PKG-INFO", "README"):
            if fname.startswith(p) or ".egg-info" in fname:
                if fname.endswith("/requires.txt"):
                    meta["deps"] = f.extractfile(info).read()
                save = False
                break

        if save:
            outfname = target + "/" + fname
            _ensure_path_exists(outfname)

            if info.type != DIRTYPE:
                this_file = f.extractfile(info)
                copyfileobj(this_file, open(outfname, "wb"))

    return meta


def _install_package(package, index, target, version, mpy, pypi):
    if (
        package.startswith("http://")
        or package.startswith("https://")
        or package.startswith("github:")
        or pypi
    ):
        if package.endswith(".py") or package.endswith(".mpy"):
            print("Downloading {} to {}".format(package, target))
            return _download_file(
                _rewrite_url(package, version), target + "/" + package.rsplit("/")[-1]
            )
        else:
            if pypi:
                this_version = version
                if not version:
                    this_version = "latest"
                print(
                    "Installing {} ({}) from {} to {}".format(package, this_version, index, target)
                )
                package = "{}/{}/json".format(index, package)
                install("utarfile")
                install("shutil")
                return _install_tar(package, index, target, version)
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


def install(package, index=None, target=None, version=None, mpy=True, pypi=False):
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

    if _install_package(package, index.rstrip("/"), target, version, mpy, pypi):
        print("Done")
    else:
        print("Package may be partially installed")
