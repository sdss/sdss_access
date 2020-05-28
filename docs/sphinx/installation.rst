
.. _install:

Installation
============

This describes the various installation methods for the SDSS sdss_access product.

Pip
---

The sdss_access product is now available as a Python package, and is pip-installable.  Simply do::

    pip install sdss-access

or to upgrage::

    pip install --upgrade sdss-access


Development
-----------
Clone the repo and run pip install::

    git clone https://github.com/sdss/sdss_access
    cd sdss_access
    pip install .[dev]

Or to run in editable mode in order to track changes from `git pulls`, run::

    pip install -e .[dev]
