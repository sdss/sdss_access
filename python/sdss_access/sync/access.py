from __future__ import absolute_import, division, print_function, unicode_literals
# The line above will help with 2to3 support.
from sdss_access.sync import CurlAccess, RsyncAccess
Base = RsyncAccess
label = 'sdss_rsync'

class Access(Base):

    def __init__(self, label=label, stream_count=5, mirror=False, public=False, release=None, verbose=False):
        super(Base, self).__init__(mirror=mirror, public=public, release=release, verbose=verbose, label = label)