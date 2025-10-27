#!/usr/bin/env python3
#
# This file is part of the MicroPython project, http://micropython.org/
#
# The MIT License (MIT)
#
# Copyright (c) 2023 Jim Mussared
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

# This script makes a CPython-compatible package from a micropython-lib package
# with a pyproject.toml that can be built (via hatch) and deployed to PyPI.
# Requires that the project sets the pypi_publish= kwarg in its metadata().

# Usage:
# ./tools/makepyproject.py --output /tmp/foo micropython/foo
# python -m build /tmp/foo
# python -m twine upload /tmp/foo/dist/*.whl

from email.utils import parseaddr
import os
import re
import shutil
import sys

from build import error_color, ensure_path_exists


DEFAULT_AUTHOR = "micropython-lib <contact@micropython.org>"
DEFAULT_LICENSE = "MIT"


def quoted_escape(s):
    return s.replace('"', '\\"')


def build(manifest_path, output_path):
    import manifestfile

    if not manifest_path.endswith(".py"):
        # Allow specifying either the directory or the manifest file explicitly.
        manifest_path = os.path.join(manifest_path, "manifest.py")

    print("Generating pyproject for {} in {}...".format(manifest_path, output_path))

    toml_path = os.path.join(output_path, "pyproject.toml")
    ensure_path_exists(toml_path)

    path_vars = {
        "MPY_LIB_DIR": os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
    }

    # .../foo/manifest.py -> foo
    package_name = os.path.basename(os.path.dirname(manifest_path))

    # Compile the manifest.
    manifest = manifestfile.ManifestFile(manifestfile.MODE_PYPROJECT, path_vars)
    manifest.execute(manifest_path)

    # If a package doesn't have a pypi name, then assume it isn't intended to
    # be publishable.
    if not manifest.metadata().pypi_publish:
        print(error_color("Error:"), package_name, "doesn't have a pypi_publish name.")
        sys.exit(1)

    # These should be in all packages eventually.
    if not manifest.metadata().version:
        print(error_color("Error:"), package_name, "doesn't have a version.")
        sys.exit(1)
    if not manifest.metadata().description:
        print(error_color("Error:"), package_name, "doesn't have a description.")
        sys.exit(1)

    # This is the root path of all .py files that are copied. We ensure that
    # they all match.
    top_level_package = None

    for result in manifest.files():
        # This isn't allowed in micropython-lib anyway.
        if result.file_type != manifestfile.FILE_TYPE_LOCAL:
            print(error_color("Error:"), "Non-local file not supported.", file=sys.stderr)
            sys.exit(1)

        # "foo/bar/baz.py" --> "foo"
        # "baz.py" --> ""
        result_package = os.path.split(result.target_path)[0]

        if not result_package:
            # This is a standalone .py file.
            print(
                error_color("Error:"),
                "Unsupported single-file module: {}".format(result.target_path),
                file=sys.stderr,
            )
            sys.exit(1)
        if top_level_package and result_package != top_level_package:
            # This likely suggests that something needs to use require(..., pypi="...").
            print(
                error_color("Error:"),
                "More than one top-level package: {}, {}.".format(
                    result_package, top_level_package
                ),
                file=sys.stderr,
            )
            sys.exit(1)
        top_level_package = result_package

        # Tag each file with the package metadata and copy the .py directly.
        with manifestfile.tagged_py_file(result.full_path, result.metadata) as tagged_path:
            dest_path = os.path.join(output_path, result.target_path)
            ensure_path_exists(dest_path)
            shutil.copyfile(tagged_path, dest_path)

    # Copy README.md if it exists
    readme_path = os.path.join(os.path.dirname(manifest_path), "README.md")
    readme_toml = ""
    if os.path.exists(readme_path):
        shutil.copyfile(readme_path, os.path.join(output_path, "README.md"))
        readme_toml = 'readme = "README.md"'

    # Apply default author and license, otherwise use the package metadata.
    license_toml = 'license = {{ text = "{}" }}'.format(
        quoted_escape(manifest.metadata().license or DEFAULT_LICENSE)
    )
    author_name, author_email = parseaddr(manifest.metadata().author or DEFAULT_AUTHOR)
    author_toml = 'authors = [ {{ name = "{}", email = "{}"}} ]'.format(
        quoted_escape(author_name), quoted_escape(author_email)
    )

    # Write pyproject.toml.
    with open(toml_path, "w") as toml_file:
        print("# Generated by makepyproject.py", file=toml_file)

        print(
            """
[build-system]
requires = [
    "hatchling"
]
build-backend = "hatchling.build"
""",
            file=toml_file,
        )

        print(
            """
[project]
name = "{}"
description = "{}"
{}
{}
version = "{}"
dependencies = [{}]
urls = {{ Homepage = "https://github.com/micropython/micropython-lib" }}
{}
""".format(
                quoted_escape(manifest.metadata().pypi_publish),
                quoted_escape(manifest.metadata().description),
                author_toml,
                license_toml,
                quoted_escape(manifest.metadata().version),
                ", ".join('"{}"'.format(quoted_escape(r)) for r in manifest.pypi_dependencies()),
                readme_toml,
            ),
            file=toml_file,
        )

        print(
            """
[tool.hatch.build]
packages = ["{}"]
""".format(top_level_package),
            file=toml_file,
        )

    print("Done.")


def main():
    import argparse

    cmd_parser = argparse.ArgumentParser(
        description="Generate a project that can be pushed to PyPI."
    )
    cmd_parser.add_argument("--output", required=True, help="output directory")
    cmd_parser.add_argument("--micropython", default=None, help="path to micropython repo")
    cmd_parser.add_argument("manifest", help="input package path")
    args = cmd_parser.parse_args()

    if args.micropython:
        sys.path.append(os.path.join(args.micropython, "tools"))  # for manifestfile

    build(args.manifest, args.output)


if __name__ == "__main__":
    main()
