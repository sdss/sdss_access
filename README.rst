===========
sdss_access
===========

This repository supports access to the SDSS data set.  See the documentation at http://sdss-access.readthedocs.io/en/latest/

| |Build Status|
| |Coverage Status|


Example usage::

    from sdss_access import SDSSPath

    sdssPath = SDSSPath()
    platelines_path = sdssPath.full('plateLines-print', plateid=12345)


.. |Build Status| image:: https://travis-ci.org/sdss/sdss_access.svg?branch=master
   :target: https://travis-ci.org/sdss/sdss_access

.. |Coverage Status| image:: https://coveralls.io/repos/github/sdss/sdss_access/badge.svg?branch=master
   :target: https://coveralls.io/github/sdss/sdss_access?branch=master

