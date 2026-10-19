# sdss_access

![Versions](https://img.shields.io/badge/python-3.11+-blue)
[![Test](https://github.com/sdss/sdss_access/actions/workflows/test.yml/badge.svg)](https://github.com/sdss/sdss_access/actions/workflows/test.yml)
[![License](https://img.shields.io/badge/License-BSD_3--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)

<!-- [![Documentation Status](https://readthedocs.org/projects/sdss_access/badge/?version=latest)](https://sdss_access.readthedocs.io/en/latest/) -->
<!-- [![codecov](https://codecov.io/gh/sdss/sdss_access/branch/main/graph/badge.svg)](https://codecov.io/gh/sdss/sdss_access) -->

Package to dynamically build filepaths and access all SDSS SAS products

## Managing your new project

After creation, your new project is ready to be used. If you answered yes to the question "Create a virtual env and sync the project after creation using uv" your project will already be synced to a virtual environment in the same directory as the project. If you need to create the venv and sync manually, go to the project directory and run:

```console
uv venv
uv sync --all-extras --all-groups
```

If you want tos specify a different Python version for the virtual environment, you can use the `--python` flag with `uv venv`, e.g.

```console
uv venv --python 3.11
```

uv will try to find the specified Python version in your system. If it can't find it, it will download an standalone version of Python and use that to create the virtual environment.

Dependencies can be added by using the `uv add` command, e.g. `uv add numpy`. You can also edit the `pyproject.toml` file directly and then run `uv sync` to install the new dependencies and update the `uv.lock` file.

Similarly, you can use `uv run` to run commands using the project virtual environment, e.g. `uv run python` to start a Python REPL with the project dependencies available, or `uv run pytest` to run the tests.

More information on how to manage your project can be found in the template [documentation](https://sdss-python-template.readthedocs.io/en/latest/index.html#developing-with-your-new-package) or in the [uv projects page](https://docs.astral.sh/uv/concepts/projects/).

## Coding standards

Before you start writing your code, make sure to read and understand the [SDSS coding standards](https://sdss-python-template.readthedocs.io/en/latest/style/STYLE_v2.html).

## Building the documentation

The template include a stub for [Sphinx](https://www.sphinx-doc.org/en/master/) documentation under `docs/sphinx`. To build the documentation locally, run the following command from the project root:

```console
sdss docs.build
```

To have the docs autobuild and watch for changes, use `nox`. To build and run the local docs server, run

```console
nox
```

This will start a local docs server on a random port. You should see something like,

```console
[sphinx-autobuild] Serving on http://127.0.0.1:54429
[sphinx-autobuild] Waiting to detect changes...
```

It should open the site automatically in a new browser window.  If `127.0.0.1:[port]` fails to load, try `localhost:[port]`.

Additional information on how to build the documentation can be found in the [docs](https://sdss-python-template.readthedocs.io/en/latest/index.html#package-documentation) section of the documentation.

## Creating Releases

New releases of `sdss-access` are created automatically, and pushed to [PyPi](https://pypi.org/project/sdss-access/), when new tags are pushed to Github.  See the [Create Release](.github/workflows/release.yml) Github Action and [Releases](https://github.com/sdss/sdss_access/releases) for the list.

New tag names follow the Python semantic versioning syntax, i.e. `X.Y.Z`.