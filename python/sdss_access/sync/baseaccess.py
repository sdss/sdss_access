from __future__ import absolute_import, division, print_function, unicode_literals
# The line above will help with 2to3 support.

from os.path import isfile, exists, dirname, join
from re import search
from sdss_access import SDSSPath, AccessError
from sdss_access.sync.auth import Auth
from sdss_access.sync.stream import Stream

class BaseAccess(SDSSPath):
    """Class for providing Rsync or Curl access to SDSS SAS Paths
    """

    def __init__(self, label=None, stream_count=5, mirror=False, public=False, release=None, verbose=False):
        super(BaseAccess, self).__init__(mirror=mirror, public=public, release=release, verbose=verbose)
        self.label = label
        self.auth = None
        self.stream = None
        self.stream_count = stream_count
        self.verbose = verbose
        self.initial_stream = self.get_stream()
        
    def get_stream(self):
        stream = Stream(stream_count=self.stream_count, verbose=self.verbose)
        return stream
        
    def set_auth(self, username=None, password=None, inquire=True):
        self.auth = Auth(public=self.public, netloc=self.netloc, verbose=self.verbose)
        self.auth.set_username(username)
        self.auth.set_password(password)
        if not self.public:
            if not self.auth.ready():
                self.auth.load()
            if not self.auth.ready():
                self.auth.set_username(inquire=inquire)
                self.auth.set_password(inquire=inquire)
                
    def reset(self):
        ''' Reset all streams '''

        # reset the main stream
        if self.stream:
            self.stream.reset()

        # reset the initial stream (otherwise old 'adds' remain in the new stream)
        if self.initial_stream:
            self.initial_stream.reset()
            
    def shuffle(self):
        self.stream.shuffle()
        
    def get_locations(self, offset=None, limit=None):
        return self.stream.get_locations(offset=offset, limit=limit) if self.stream else None
        
    def get_paths(self, offset=None, limit=None):
        locations = self.get_locations(offset=offset, limit=limit)
        paths = [join(self.base_dir, location) for location in locations] if locations else None
        return paths
        
    def get_urls(self, offset=None, limit=None):
        locations = self.get_locations(offset=offset, limit=limit)
        remote_base = self.get_remote_base()
        sasdir = 'sas' if not self.public else ''
        urls = [join(remote_base, sasdir, location) for location in locations] if locations else None
        return urls
        
