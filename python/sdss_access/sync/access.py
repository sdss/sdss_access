from __future__ import absolute_import, division, print_function, unicode_literals

# The line above will help with 2to3 support.
from sdss_access.sync import CurlAccess, RsyncAccess
from sdss_access import is_posix

Base = RsyncAccess if is_posix else CurlAccess
label = 'sdss_rsync' if is_posix else 'sdss_curl'

class Access(Base):
    """Class for providing Rsync or Curl access depending on posix
    """
    def __init__(self, label=label, stream_count=5, mirror=False, public=False, release=None, verbose=False):
        super(Base, self).__init__(mirror=mirror, public=public, release=release, verbose=verbose, label = label)