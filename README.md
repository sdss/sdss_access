# sdss_access

![Versions](https://img.shields.io/badge/python->3.7-blue)
[![Documentation Status](https://readthedocs.org/projects/sdss-access/badge/?version=latest)](https://sdss-access.readthedocs.io/en/latest/?badge=latest)
[![Travis (.org)](https://img.shields.io/travis/sdss/sdss_access)](https://travis-ci.org/sdss/sdss_access)
[![codecov](https://codecov.io/gh/sdss/sdss_access/branch/master/graph/badge.svg)](https://codecov.io/gh/sdss/sdss_access)
[![Coveralls](https://coveralls.io/repos/github/sdss/sdss_access/badge.svg)](https://coveralls.io/github/sdss/sdss_access)


This products allows for dynamically building filepaths to SDSS data products hosted on the Science Archive Server (SAS).  Filepaths
are dynamically constructed given a minimal name and set of keywords to be substituted via a string templating system.  Data products
can also be downloaded programmatically using an ``Access`` class which provides streaming downloads via ``rysnc`` or ``curl``
depending on your OS. See the full documentation at http://sdss-access.readthedocs.io/en/latest/

Useful links
------------

- GitHub: https://github.com/sdss/sdss_access
- Documentation: https://sdss-access.readthedocs.org
- Issues: https://github.com/sdss/sdss_access/issues


