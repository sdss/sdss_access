===========
sdss_access
===========

This repository supports access to the SDSS data set. 

Example usage::

    from sdss_access import SDSSPath
    
    sdssPath = SDSSPath()
    platelines_path = sdssPath.full('plateLines-print', plateid=12345)


