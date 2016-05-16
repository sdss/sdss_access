from os import makedirs
from os.path import isfile, exists, dirname, join
from re import search
from sdss_access import SDSSPath
from sdss_access.sync.auth import Auth
from sdss_access.sync.stream import Stream

class RsyncAccess(SDSSPath):
    
    public_remote_base = 'rsync://data.sdss.org:'
    sdss_remote_base = 'rsync://sdss@dtn01.sdss.org:'

    def __init__(self, label='sdss_rsync', stream_count=5, verbose=False):
        super(RsyncAccess, self).__init__()
        self.label = label
        self.stream_count = stream_count
        self.verbose = verbose
        self.initial_stream = self.get_stream()
    
    def get_stream(self):
        stream = Stream(stream_count=self.stream_count, verbose=self.verbose)
        stream.reset_streamlet()
        return stream

    def remote(self, public=False):
        self.set_auth(public=public)
        self.remote_base = self.public_remote_base if public else self.sdss_remote_base
    
    def set_auth(self, public=False, username=None, password=None):
        self.auth = Auth(public=public, host=self.host)
        self.auth.set_username(username)
        self.auth.set_password(password)
        if not self.auth.ready(): self.auth.load()

    def add(self, filetype, **kwargs):
        location = self.location(filetype, **kwargs)
        source = self.url(filetype, **kwargs)
        destination = self.full(filetype, **kwargs)
        if location and source and destination:
            self.initial_stream.append_task(location=location, source=source, destination=destination)
        else: print("There is no file with filetype=%r to access in the tree module loaded" % filetype)

    def set_stream(self):
        self.stream = self.get_stream()
        self.stream.source =  join(self.remote_base, 'sas') if self.remote_base else None
        self.stream.destination = self.base_dir
        if self.stream.source and self.stream.destination:
            for location,source,destination in self.initial_stream.task:
                self.set_stream_task(source=source,depth=location.count('/'))
                    
    def set_stream_task(self,source=None,depth=None):
        if source and depth:
            if self.verbose: print "PATH %s" % source
            command = "rsync -R {source}".format(source=source)
            status, out, err = self.stream.cli.foreground_run(command)
            if status: raise self.stream.cliError("Error: %s [code:%r]" % (err,status))
            else:
                for result in out.split("\n"):
                    try: location = search(r"^.*\s{1,3}(.+)$",result).group(1)
                    except: location = None
                    if location and location.count('/')==depth:
                        source = join(self.stream.source, location) if self.remote_base else None
                        destination = join(self.stream.destination, location)
                        self.stream.append_task(location=location, source=source, destination=destination)

    def shuffle(self): self.stream.shuffle()

    def get_locations(self, offset=None, limit=None):
        return self.stream.get_locations(offset=offset,limit=limit) if self.stream else None

    def get_paths(self, offset=None, limit=None):
        locations = self.get_locations(offset=offset,limit=limit)
        paths = [join(self.base_dir, location) for location in locations] if locations else None
        return paths
    
    def get_urls(self, offset=None, limit=None):
        locations = self.get_locations(offset=offset,limit=limit)
        host_url = self.get_host_url()
        urls = [join(host_url, 'sas', location) for location in locations] if locations else None
        return urls

    def commit(self, dryrun=False):
        self.stream.env = {'RSYNC_PASSWORD':self.auth.password} if self.auth.ready() else None
        self.stream.command = "rsync -avR --files-from={path} {source} {destination}"
        self.stream.commit_tasks()
        self.stream.run_tasks()
    
