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
apply [as for the main MicroPython repository](https://github.com/micropython/micropython/blob/master/CODECONVENTIONS.md).

All Python code is formatted using the [black](https://github.com/psf/black)
tool. You can run [`tools/codeformat.py`](tools/codeformat.py) to apply
`black` automatically before submitting a PR. The GitHub CI will also run the
[ruff](https://github.com/astral-sh/ruff) tool to apply further "linting"
checks.

Similar to the main repository, a configuration is provided for the
[pre-commit](https://pre-commit.com/) tool to apply `black` code formatting
rules and run `ruff` automatically. See the documentation for using pre-commit
in [the code conventions document](https://github.com/micropython/micropython/blob/master/CODECONVENTIONS.md#automatic-pre-commit-hooks)

In addition to the conventions from the main repository, there are some
specific conventions and guidelines for micropython-lib:

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

* To make it easier for others to install packages directly from your PR before
  it is merged, consider opting-in to automatic package publishing (see
  [Publishing packages from forks](#publishing-packages-from-forks)). If you do
  this, consider quoting the [commands to install
  packages](README.md#installing-packages-from-forks) in your Pull Request
  description.

### Publishing packages from forks

You can easily publish the packages from your micropython-lib
[fork](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/about-forks)
by opting in to a system based on [GitHub
Actions](https://docs.github.com/en/actions) and [GitHub
Pages](https://docs.github.com/en/pages):

1. Open your fork's repository in the GitHub web interface.
2. Navigate to "Settings" -> "Secrets and variables" -> "Actions" -> "Variables".
3. Click "New repository variable"
4. Create a variable named `MICROPY_PUBLISH_MIP_INDEX` with value `true` (or any
   "truthy" value).
5. The settings for GitHub Actions and GitHub Pages features should not need to
   be changed from the repository defaults, unless you've explicitly disabled
   Actions or Pages in your fork.

The next time you push commits to a branch in your fork, GitHub Actions will run
an additional step in the "Build All Packages" workflow named "Publish Packages
for branch". This step runs in *your fork*, but if you open a pull request then
this workflow is not shown in the Pull Request's "Checks". These run in the
upstream repository. Navigate to your fork's Actions tab in order to see
the additional "Publish Packages for branch" step.

Anyone can then install these packages as described under [Installing packages
from forks](README.md#installing-packages-from-forks).

The exact command is also quoted in the GitHub Actions log in your fork's
Actions for the "Publish Packages for branch" step of "Build All Packages".

#### Opting Back Out

To opt-out again, delete the `MICROPY_PUBLISH_MIP_INDEX` variable and
(optionally) delete the `gh-pages` branch from your fork.

*Note*: While enabled, all micropython-lib packages will be published each time
a change is pushed to any branch in your fork. A commit is added to the
`gh-pages` branch each time. In a busy repository, the `gh-pages` branch may
become quite large. The actual `.git` directory size on disk should still be
quite small, as most of the content will be duplicated. If you're worried that
the `gh-pages` branch has become too large then you can always delete this
branch from GitHub. GitHub Actions will create a new `gh-pages` branch the next
time you push a change.
