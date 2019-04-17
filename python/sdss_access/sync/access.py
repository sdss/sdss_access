from __future__ import absolute_import, division, print_function, unicode_literals
# The line above will help with 2to3 support.
from sdss_access.sync import CurlAccess, RsyncAccess, AccessError

class Access: pass

#Access.__dict__ = dict(RsyncAccess.__dict__)
