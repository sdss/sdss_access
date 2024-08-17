# sdss_access

![Versions](https://img.shields.io/badge/python->3.7-blue)
[![Documentation Status](https://readthedocs.org/projects/sdss-access/badge/?version=latest)](https://sdss-access.readthedocs.io/en/latest/?badge=latest)
[![Build Sphinx Documentation](https://github.com/sdss/sdss_access/actions/workflows/sphinxbuild.yml/badge.svg)](https://github.com/sdss/sdss_access/actions/workflows/sphinxbuild.yml)
[![Build and Test](https://github.com/sdss/sdss_access/actions/workflows/build.yml/badge.svg)](https://github.com/sdss/sdss_access/actions/workflows/build.yml)
[![codecov](https://codecov.io/gh/sdss/sdss_access/branch/master/graph/badge.svg)](https://codecov.io/gh/sdss/sdss_access)


This products allows for dynamically building filepaths to SDSS data products hosted on the Science Archive Server (SAS).  Filepaths
are dynamically constructed given a minimal name and set of keywords to be substituted via a string templating system.  Data products
can also be downloaded programmatically using an ``Access`` class which provides streaming downloads via ``rysnc`` or ``curl``
depending on your OS. See the full documentation at http://sdss-access.readthedocs.io/en/latest/

## Developer Install

To install `sdss_access` for development locally:

```
git clone https://github.com/sdss/sdss_access
cd sdss_access
pip install -e ".[dev,docs]"
```

## Build Sphinx Docs

Within the top level repo directory, run the `sdsstools` commands:
```
# build the Sphinx documentation
sdss docs.build

# open the docs locally in a browser
sdss docs.show
```
Documentation is automatically built and pushed to Read The Docs.

## Testing
Tests are created using `pytest`.  Navigate to the `tests` directory from the top level and run with `pytest`.
```
cd tests
pytest
```

## Creating Releases

New releases of `sdss-access` are created automatically, and pushed to [PyPi](https://pypi.org/project/sdss-access/), when new tags are pushed to Github.  See the [Create Release](.github/workflows/release.yml) Github Action and [Releases](https://github.com/sdss/sdss_access/releases) for the list.

New tag names follow the Python semantic versioning syntax, i.e. `X.Y.Z`.

# Useful links

- GitHub: https://github.com/sdss/sdss_access
- Documentation: https://sdss-access.readthedocs.org
- Issues: https://github.com/sdss/sdss_access/issues


