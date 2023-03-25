# MicroPython package installer
# MIT license
# Copyright (c) 2023 Jonas Scharpf (brainelectronics)

import gc
import sys
from binascii import hexlify
from hashlib import sha256
from os import mkdir, stat, unlink
from shutil import copyfileobj

import urequests as requests
from utarfile import DIRTYPE, TarFile
from uzlib import DecompIO

_PACKAGE_INDEX = const("https://pypi.org/pypi")
_CHUNK_SIZE = 128


class _Subscriptable:
    def __getitem__(self, item) -> None:
        return None


_subscriptable = _Subscriptable()

Optional = _subscriptable
Callable = _subscriptable


# This implements os.makedirs(os.dirname(path))
def _ensure_path_exists(path: str) -> None:
    split = path.split("/")

    # Handle paths starting with "/".
    if not split[0]:
        split.pop(0)
        split[0] = "/" + split[0]

    prefix = ""
    for i in range(len(split) - 1):
        prefix += split[i]
        try:
            stat(prefix)
        except:
            mkdir(prefix)
        prefix += "/"


# Copy from src (stream) to dest (function-taking-bytes)
def _chunk(src: Callable, dest: Callable) -> None:
    buf = memoryview(bytearray(_CHUNK_SIZE))
    while True:
        n = src.readinto(buf)
        if n == 0:
            break
        dest(buf if n == _CHUNK_SIZE else buf[:n])


def _download_file(url: str, dest: str) -> bool:
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


# Check if the hash of the specified path matches the hash.
def _verify_file(path: str, digests_256: str) -> bool:
    try:
        with open(path, "rb") as f:
            hs256 = sha256()
            _chunk(f, hs256.update)
            existing_hash = str(hexlify(hs256.digest())[: len(digests_256)], "utf-8")
            return existing_hash == digests_256
    except Exception as e:
        print("Failed to verify file {} hash {} due to {}".format(path, digests_256, e))
        return False


def _get_package_json(package_json_url: str) -> dict:
    package_json = {}
    response = requests.get(package_json_url)
    try:
        if response.status_code != 200:
            print("Package not found:", package_json_url)
            return package_json

        package_json = response.json()
    finally:
        response.close()

    return package_json


def _get_version_info(package_json_url: str, version: str) -> dict:
    version_info = {}
    package_json = _get_package_json(package_json_url=package_json_url)

    if not package_json:
        return version_info

    if not version:
        # get latest version from info property
        version = package_json.get("info", {}).get("version", "")

        if version not in package_json.get("releases", ()):
            print("Version {} not found".format(version))
            return version_info

        # Use last element to get ".tar.gz" in case ".wheel" is also available
        version_info = package_json["releases"][version][-1]
    else:
        # specific version given, lookup directly in urls property
        # Use last element to get ".tar.gz" in case ".wheel" is also available
        version_info = package_json["urls"][-1]

    return version_info


def _install_tar(
    package_json_url: str, index: Optional[str], target: str, version: Optional[str]
) -> bool:
    meta = {}

    version_info = _get_version_info(package_json_url=package_json_url, version=version)
    if not version_info:
        return False

    package_url = version_info.get("url", "")
    package_sha256 = version_info.get("digests", {}).get("sha256", "")

    # save some memory, the large dict is no longer required
    del version_info
    gc.collect()

    fs_target_path = target + "/" + package_url.rsplit("/", 1)[1]

    if not _download_file(url=package_url, dest=fs_target_path):
        print("Failed to download {} to {}".format(package_url, fs_target_path))
        return False

    if package_sha256:
        if not _verify_file(path=fs_target_path, digests_256=package_sha256):
            print("Mismatch between calculated and given SHA256 of downloaded file")
            return False
    else:
        print("SHA256 digest not found, downloaded file might be unverified")

    try:
        gzdict_sz = 16 + 15
        sz = gc.mem_free() + gc.mem_alloc()
        if sz <= 65536:
            gzdict_sz = 16 + 12

        zipped_file = open(fs_target_path, "rb")
        decompressed_file = DecompIO(zipped_file, gzdict_sz)
        tar_file = TarFile(fileobj=decompressed_file)

        meta = _install_tar_file(f=tar_file, target=target)

        zipped_file.close()
        del zipped_file
        del decompressed_file
        del tar_file
    except Exception as e:
        print("Failed to decompress downloaded file due to {}".format(e))
        return False

    # cleanup downloaded file
    try:
        unlink(fs_target_path)
    except Exception as e:
        print("Error during cleanup of {}".format(fs_target_path), e)

    gc.collect()

    deps = meta.get("deps", "").rstrip()
    if deps:
        return _handle_dependencies(deps=deps, index=index, target=target)

    return True


def _handle_dependencies(deps: dict, index: str, target: str) -> bool:
    deps = deps.decode("utf-8").split("\n")
    print("Install additional deps: {}".format(deps))
    results = []

    for ele in deps:
        res = _install_package(package=ele, index=index, target=target, version=None)
        if not res:
            print("Package may be partially installed")
        results.append(res)

    return all(results)


def _install_tar_file(f: TarFile, target: str) -> dict:
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


def _install_package(
    package: str, index: Optional[str], target: Optional[str], version: Optional[str]
) -> bool:
    # https://warehouse.pypa.io/api-reference/json.html
    this_version = version
    if not version:
        this_version = "latest"
        # /pypi/<project_name>/json
        package_url = "{}/{}/json".format(index, package)
    else:
        # /pypi/<project_name>/<version>/json
        package_url = "{}/{}/{}/json".format(index, package, version)

    print("Installing {} ({}) from {} to {}".format(package, this_version, index, target))

    return _install_tar(package_json_url=package_url, index=index, target=target, version=version)


def install(
    package: str,
    index: Optional[str] = None,
    target: Optional[str] = None,
    version: Optional[str] = None,
) -> None:
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

    if _install_package(package=package, index=index.rstrip("/"), target=target, version=version):
        print("Done")
    else:
        print("Package may be partially installed")
