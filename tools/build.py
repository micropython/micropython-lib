#!/usr/bin/env python3
#
# This file is part of the MicroPython project, http://micropython.org/
#
# The MIT License (MIT)
#
# Copyright (c) 2022 Jim Mussared
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

# This script compiles all packages in this repository (excluding unix-ffi)
# into a directory suitable for serving to "mip" via a static web server.

# Usage:
# ./tools/build.py --output /tmp/micropython-lib/v2

# The output directory (--output) will have the following layout
# /
#   index.json
#   file/
#     1d/
#       1dddc25d
#     c3/
#       c31d7eb7
#       c3a3934b
#     e3/
#       e39dbf64
#     ...
#   package/
#     6/                 <-- mpy version
#       aioble/
#         latest.json
#         0.1.json
#         ...
#       hmac/
#         latest.json
#         3.4.2-3.json
#         ...
#       pyjwt/
#         latest.json
#         0.1.json
#         ...
#     7/                 <-- other mpy versions
#       ...
#     py/                <-- "source" distribution
#       ...
#     ...

# index.json is:
# {
#   "v": 2,                      <-- file format version
#   "updated": <utc-seconds-since-1970>,
#   "packages": {
#     {
#       "name": "aioble",
#       "version": "0.1",        <-- Latest version of this package (always present, may be empty).
#       "author": "",            <-- Optional author (always present, may be empty).
#       "description": "...",    <-- Optional description (always present, may be empty).
#       "license": "MIT",        <-- SPDX short identifier (required).
#       "versions": {
#         "6": ["0.1", "0.2"],
#         "7": ["0.2", "0.3", "0.4"],
#         ...                    <-- Other bytecode versions
#         "py": ["0.1", "0.2", "0.3", "0.4"]
#       },
#       // The following entries were added in file format version 2.
#       path: "micropython/bluetooth/aioble",
#     },
#     ...
#   }
# }

# Each file in the "file" directory is the file contents (usually .mpy), named
# by the prefix of the sha256 hash of the contents. Files are never removed, and
# collisions are detected and will fail the compile, and the prefix length should
# be increased.
# As of September 2022, there are no collisions with a hash prefix length of 4,
# so the default of 8 should be sufficient for a while. Increasing the length
# doesn't invalidate old packages.

# Each package json (either latest.json or {version}.json) is:
# {
#   "v": 1,     <-- file format version
#   "hashes": [
#     ["aioble/server.mpy", "e39dbf64"],
#     ...
#   ],
#   "urls": [   <-- not used by micropython-lib packages
#     ["target/path.py", "http://url/foo/bar/path.py"],
#     ...
#   ],
#   "deps": [   <-- not used by micropython-lib packages
#     ["name", "version"],
#     ...
#   ]
#   "version": "0.1"
# }

# mip (or other tools) should request /package/{mpy_version}/{package_name}/{version}.json.

import glob
import hashlib
import json
import os
import shutil
import sys
import tempfile
import time


_JSON_VERSION_INDEX = 2
_JSON_VERSION_PACKAGE = 1


_COLOR_ERROR_ON = "\033[1;31m"
_COLOR_ERROR_OFF = "\033[0m"


# Create all directories in the path (such that the file can be created).
def ensure_path_exists(file_path):
    path = os.path.dirname(file_path)
    if not os.path.isdir(path):
        os.makedirs(path)


# Returns the sha256 of the specified file object.
def _get_file_hash(f):
    hs256 = hashlib.sha256()
    hs256.update(f.read())
    return hs256.hexdigest()


# Returns true if the two files contain identical contents.
def _identical_files(path_a, path_b):
    with open(path_a, "rb") as fa:
        with open(path_b, "rb") as fb:
            return fa.read() == fb.read()


# Helper to write the object as json to the specified path, creating any
# directories as required.
def _write_json(obj, path, minify=False):
    ensure_path_exists(path)
    with open(path, "w") as f:
        json.dump(
            obj, f, indent=(None if minify else 2), separators=((",", ":") if minify else None)
        )
        f.write("\n")


# Write the package json to package/{"py" or mpy_version}/{package}/{version}.json.
def _write_package_json(
    package_json, out_package_dir, mpy_version, package_name, version, replace
):
    path = os.path.join(out_package_dir, mpy_version, package_name, version + ".json")
    if replace or not os.path.exists(path):
        _write_json(package_json, path, minify=True)


# Format s with bold red.
def error_color(s):
    return _COLOR_ERROR_ON + s + _COLOR_ERROR_OFF


# Copy src to "file"/{short_hash[0:2]}/{short_hash}.
def _write_hashed_file(package_name, src, target_path, out_file_dir, hash_prefix_len):
    # Generate the full sha256 and the hash prefix to use as the output path.
    file_hash = _get_file_hash(src)
    short_file_hash = file_hash[:hash_prefix_len]
    # Group files into subdirectories using the first two bytes of the hash prefix.
    output_file = os.path.join(short_file_hash[:2], short_file_hash)
    output_file_path = os.path.join(out_file_dir, output_file)

    if os.path.exists(output_file_path):
        # If the file exists (e.g. from a previous run of this script), then ensure
        # that it's actually the same file.
        if not _identical_files(src.name, output_file_path):
            print(
                error_color("Hash collision processing:"),
                package_name,
                file=sys.stderr,
            )
            print("  File:        ", target_path, file=sys.stderr)
            print("  Short hash:  ", short_file_hash, file=sys.stderr)
            print("  Full hash:   ", file_hash, file=sys.stderr)
            with open(output_file_path, "rb") as f:
                print("  Target hash: ", _get_file_hash(f), file=sys.stderr)
            print("Try increasing --hash-prefix (currently {})".format(hash_prefix_len))
            sys.exit(1)
    else:
        # Create new file.
        ensure_path_exists(output_file_path)
        shutil.copyfile(src.name, output_file_path)

    return short_file_hash


# Convert the tagged .py file into a .mpy file and copy to the "file" output
# directory with it's hashed name. Updates the package_json with the file
# hash.
def _compile_as_mpy(
    package_name,
    package_json,
    tagged_path,
    target_path,
    opt,
    mpy_cross,
    mpy_cross_path,
    out_file_dir,
    hash_prefix_len,
):
    with tempfile.NamedTemporaryFile(mode="rb", suffix=".mpy", delete=True) as mpy_tempfile:
        try:
            mpy_cross.compile(
                tagged_path,
                dest=mpy_tempfile.name,
                src_path=target_path,
                opt=opt,
                mpy_cross=mpy_cross_path,
            )
        except mpy_cross.CrossCompileError as e:
            print(
                error_color("Error:"),
                "Unable to compile",
                target_path,
                "in package",
                package_name,
                file=sys.stderr,
            )
            print(e)
            sys.exit(1)

        short_mpy_hash = _write_hashed_file(
            package_name, mpy_tempfile, target_path, out_file_dir, hash_prefix_len
        )

        # Add the file to the package json.
        target_path_mpy = target_path[:-2] + "mpy"
        package_json["hashes"].append((target_path_mpy, short_mpy_hash))


# Copy the tagged .py file to the "file" output directory with it's hashed
# name. Updates the package_json with the file hash.
def _copy_as_py(
    package_name, package_json, tagged_path, target_path, out_file_dir, hash_prefix_len
):
    with open(tagged_path, "rb") as tagged_file:
        short_py_hash = _write_hashed_file(
            package_name, tagged_file, target_path, out_file_dir, hash_prefix_len
        )
    # Add the file to the package json.
    package_json["hashes"].append((target_path, short_py_hash))


# Update to the latest metadata, and add any new versions to the package in
# the index json.
def _update_index_package_metadata(index_package_json, metadata, mpy_version, package_path):
    index_package_json["version"] = metadata.version or ""
    index_package_json["author"] = ""  # TODO: Make manifestfile.py capture this.
    index_package_json["description"] = metadata.description or ""
    index_package_json["license"] = metadata.license or "MIT"
    if "versions" not in index_package_json:
        index_package_json["versions"] = {}
    if metadata.version:
        for v in ("py", mpy_version):
            if v not in index_package_json["versions"]:
                index_package_json["versions"][v] = []
            if metadata.version not in index_package_json["versions"][v]:
                print("  New version {}={}".format(v, metadata.version))
                index_package_json["versions"][v].append(metadata.version)

    # The following entries were added in file format version 2.
    index_package_json["path"] = package_path


def build(output_path, hash_prefix_len, mpy_cross_path):
    import manifestfile
    import mpy_cross

    out_file_dir = os.path.join(output_path, "file")
    out_package_dir = os.path.join(output_path, "package")

    path_vars = {
        "MPY_LIB_DIR": os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
    }

    index_json_path = os.path.join(output_path, "index.json")

    try:
        with open(index_json_path) as f:
            print("Updating existing index.json")
            index_json = json.load(f)
    except FileNotFoundError:
        print("Creating new index.json")
        index_json = {"packages": []}

    index_json["v"] = _JSON_VERSION_INDEX
    index_json["updated"] = int(time.time())

    # For now, don't process unix-ffi. In the future this can be extended to
    # allow a way to request unix-ffi packages via mip.
    lib_dirs = ["micropython", "python-stdlib", "python-ecosys"]

    mpy_version, _mpy_sub_version = mpy_cross.mpy_version(mpy_cross=mpy_cross_path)
    mpy_version = str(mpy_version)
    print("Generating bytecode version", mpy_version)

    for lib_dir in lib_dirs:
        for manifest_path in glob.glob(os.path.join(lib_dir, "**", "manifest.py"), recursive=True):
            package_path = os.path.dirname(manifest_path)
            print("{}".format(package_path))
            # .../foo/manifest.py -> foo
            package_name = os.path.basename(os.path.dirname(manifest_path))

            # Compile the manifest.
            manifest = manifestfile.ManifestFile(manifestfile.MODE_COMPILE, path_vars)
            manifest.execute(manifest_path)

            # Append this package to the index.
            if not manifest.metadata().version:
                print(error_color("Warning:"), package_name, "doesn't have a version.")

            # Try to find this package in the previous index.json.
            for p in index_json["packages"]:
                if p["name"] == package_name:
                    index_package_json = p
                    break
            else:
                print("  First-time package")
                index_package_json = {
                    "name": package_name,
                }
                index_json["packages"].append(index_package_json)

            _update_index_package_metadata(
                index_package_json, manifest.metadata(), mpy_version, package_path
            )

            # This is the package json that mip/mpremote downloads.
            mpy_package_json = {
                "v": _JSON_VERSION_PACKAGE,
                "hashes": [],
                "version": manifest.metadata().version or "",
            }
            py_package_json = {
                "v": _JSON_VERSION_PACKAGE,
                "hashes": [],
                "version": manifest.metadata().version or "",
            }

            for result in manifest.files():
                # This isn't allowed in micropython-lib anyway.
                if result.file_type != manifestfile.FILE_TYPE_LOCAL:
                    print(error_color("Error:"), "Non-local file not supported.", file=sys.stderr)
                    sys.exit(1)

                if not result.target_path.endswith(".py"):
                    print(
                        error_color("Error:"),
                        "Target path isn't a .py file:",
                        result.target_path,
                        file=sys.stderr,
                    )
                    sys.exit(1)

                # Tag each file with the package metadata and compile to .mpy
                # (and copy the .py directly).
                with manifestfile.tagged_py_file(result.full_path, result.metadata) as tagged_path:
                    _compile_as_mpy(
                        package_name,
                        mpy_package_json,
                        tagged_path,
                        result.target_path,
                        result.opt,
                        mpy_cross,
                        mpy_cross_path,
                        out_file_dir,
                        hash_prefix_len,
                    )
                    _copy_as_py(
                        package_name,
                        py_package_json,
                        tagged_path,
                        result.target_path,
                        out_file_dir,
                        hash_prefix_len,
                    )

            # Create/replace {package}/latest.json.
            _write_package_json(
                mpy_package_json,
                out_package_dir,
                mpy_version,
                package_name,
                "latest",
                replace=True,
            )
            _write_package_json(
                py_package_json, out_package_dir, "py", package_name, "latest", replace=True
            )

            # Write {package}/{version}.json, but only if it doesn't already
            # exist. A package version is "locked" the first time it's seen
            # by this script.
            if manifest.metadata().version:
                _write_package_json(
                    mpy_package_json,
                    out_package_dir,
                    mpy_version,
                    package_name,
                    manifest.metadata().version,
                    replace=False,
                )
                _write_package_json(
                    py_package_json,
                    out_package_dir,
                    "py",
                    package_name,
                    manifest.metadata().version,
                    replace=False,
                )

    # Write updated package index json, sorted by package name.
    index_json["packages"].sort(key=lambda p: p["name"])
    _write_json(index_json, index_json_path, minify=False)


def main():
    import argparse

    cmd_parser = argparse.ArgumentParser(description="Compile micropython-lib for serving to mip.")
    cmd_parser.add_argument("--output", required=True, help="output directory")
    cmd_parser.add_argument("--hash-prefix", default=8, type=int, help="hash prefix length")
    cmd_parser.add_argument("--mpy-cross", default=None, help="optional path to mpy-cross binary")
    cmd_parser.add_argument("--micropython", default=None, help="path to micropython repo")
    args = cmd_parser.parse_args()

    if args.micropython:
        sys.path.append(os.path.join(args.micropython, "tools"))  # for manifestfile
        sys.path.append(os.path.join(args.micropython, "mpy-cross"))  # for mpy_cross

    build(args.output, hash_prefix_len=max(4, args.hash_prefix), mpy_cross_path=args.mpy_cross)


if __name__ == "__main__":
    main()
