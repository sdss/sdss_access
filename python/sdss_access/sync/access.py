from __future__ import absolute_import, division, print_function, unicode_literals

# The line above will help with 2to3 support.
from sdss_access.sync import CurlAccess, RsyncAccess
from sdss_access import is_posix

Base = RsyncAccess if is_posix else CurlAccess
access_mode = 'rsync' if is_posix else 'curl'
label = 'sdss_{0}'.format(access_mode)


class Access(Base):
    """Class for providing Rsync or Curl access depending on posix
    """
    access_mode = access_mode

    def __repr__(self):
        return '<Access(access_mode="{0}", using="{1}")>'.format(self.access_mode, self.netloc)

