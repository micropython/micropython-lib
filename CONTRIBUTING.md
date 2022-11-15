## Contributor's Guidelines & Code Conventions

micropython-lib follows the same general conventions as the [main MicroPython
repository](https://github.com/micropython/micropython). Please see
[micropython/CONTRIBUTING.md](https://github.com/micropython/micropython/blob/master/CONTRIBUTING.md)
and [micropython/CODECONVENTIONS.md](https://github.com/micropython/micropython/blob/master/CODECONVENTIONS.md).

### Raising issues

Please include enough information for someone to reproduce the issue you are
describing. This will typically include:

* The version of MicroPython you are using (e.g. the firmware filename, git
  hash, or version info printed by the startup message).
* What board/device you are running MicroPython on.
* Which package you have installed, how you installed it, and what version.
  When installed via `mip`, all packages will have a `__version__`
  attribute.
* A simple code snippet that demonstrates the issue.

If you have a how-to question or are looking for help with using MicroPython
or packages from micropython-lib, please post at the
[discussion forum](https://github.com/orgs/micropython/discussions) instead.

### Pull requests

The same rules for commit messages, signing-off commits, and commit structure
apply as for the main MicroPython repository. All Python code is formatted
using `black`. See [`tools/codeformat.py`](tools/codeformat.py) to apply
`black` automatically before submitting a PR.

There are some specific conventions and guidelines for micropython-lib:

* The first line of the commit message should start with the name of the
  package, followed by a short description of the commit. Package names are
  globally unique in the micropython-lib directory structure.

  For example: `shutil: Add disk_usage function.`

* Although we encourage keeping the code short and minimal, please still use
  comments in your code. Typically, packages will be installed via
  `mip` and so they will be compiled to bytecode where comments will
  _not_ contribute to the installed size.

* All packages must include a `manifest.py`, including a `metadata()` line
  with at least a description and a version.

* Prefer to break larger packages up into smaller chunks, so that just the
  required functionality can be installed. The way to do this is to have a
  base package, e.g. `mypackage` containing `mypackage/__init__.py`, and then
  an "extension" package, e.g. `mypackage-ext` containing additional files
  e.g. `mypackage/ext.py`. See
  [`collections-defaultdict`](python-stdlib/collections-defaultdict) as an
  example.

* If you think a package might be extended in this way in the future, prefer
  to create a package directory with `package/__init__.py`, rather than a
  single `module.py`.

* Packages in the python-stdlib directory should be CPython compatible and
  implement a subset of the CPython equivalent. Avoid adding
  MicroPython-specific extensions. Please include a link to the corresponding
  CPython docs in the PR.

* Include tests (ideally using the `unittest` package) as `test_*.py`.
  Otherwise, provide examples as `example_*.py`. When porting CPython
  packages, prefer to use the existing tests rather than writing new ones
  from scratch.

* When porting an existing third-party package, please ensure that the source
  license is compatible.
