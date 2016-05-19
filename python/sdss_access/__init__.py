# License information goes here
# -*- coding: utf-8 -*-
"""
===========
sdss_access
===========

The function sdss4tools.install.version() should be used to set the ``__version__``
package variable.  In order for this to work properly, the svn property
svn:keywords must be set to HeadURL on this file.

.. SDSS-IV: http://trac.sdss.org
.. Python:  http://python.org
"""
#
from __future__ import absolute_import, division, print_function, unicode_literals
# The line above will help with 2to3 support.
#from sdss4tools.install import version
#
# Set version string.
#
#__version__ = version('$HeadURL$')
#
# Clean up namespace
#
#del version
__version__ = "trunk"

from .path import Path as SDSSPath, AccessError
from .sync import HttpAccess, RsyncAccess
