from __future__ import absolute_import, division, print_function, unicode_literals
# The line above will help with 2to3 support.

from os.path import isfile, exists, dirname, join
from re import search
from sdss_access import AccessError
from sdss_access.sync.baseaccess import BaseAccess
from sdss_access.sync.auth import Auth
from sdss_access.sync.stream import Stream


class RsyncAccess(BaseAccess):
    """Class for providing Rsync access to SDSS SAS Paths
    """

    def __init__(self, label='sdss_rsync', stream_count=5, mirror=False, public=False, release=None, verbose=False):
        super(RsyncAccess, self).__init__(mirror=mirror, public=public, release=release, verbose=verbose)
        self.label = label
        self.auth = None
        self.stream = None
        self.stream_count = stream_count
        self.verbose = verbose
        self.initial_stream = self.get_stream()

    def remote(self, username=None, password=None, inquire=None):
        """ Configures remote access """

        self.set_netloc(sdss=True)  # simplifies things to have a single sdss machine in .netrc
        self.set_auth(username=username, password=password, inquire=inquire)
        self.set_netloc(dtn=not self.public)
        self.set_remote_base(scheme="rsync")
        
    def add(self, filetype, **kwargs):
        """ Adds a filepath into the list of tasks to download"""

        location = self.location(filetype, **kwargs)
        source = self.url(filetype, sasdir='sas' if not self.public else '', **kwargs)
        if 'full' not in kwargs:
            destination = self.full(filetype, **kwargs)
        else:
            destination = kwargs.get('full')

        if location and source and destination:
            self.initial_stream.append_task(location=location, source=source, destination=destination)
        else:
            print("There is no file with filetype=%r to access in the tree module loaded" % filetype)

    def set_stream(self):
        """ Sets the download streams """

        if not self.auth:
            raise AccessError("Please use the remote() method to set rsync authorization or use remote(public=True) for public data")
        elif not self.initial_stream.task:
            raise AccessError("No files to download.")
        else:
            self.stream = self.get_stream()
            self.stream.source = join(self.remote_base, 'sas') if self.remote_base and not self.public else join(self.remote_base, self.release) if self.release else self.remote_base
            self.stream.destination = join(self.base_dir, self.release) if self.public and self.release else self.base_dir
            self.stream.cli.env = {'RSYNC_PASSWORD': self.auth.password} if self.auth.ready() else None
            if self.stream.source and self.stream.destination:
                for task in self.initial_stream.task:
                    self.set_stream_task(task)
            ntask = len(self.stream.task)
            if self.stream.stream_count > ntask:
                if self.verbose:
                    print("SDSS_ACCESS> Reducing the number of streams from %r to %r, the number of download tasks." % (self.stream.stream_count, ntask))
                self.stream.stream_count = ntask
                self.stream.streamlet = self.stream.streamlet[:ntask]

    def get_task_out(self, task=None):
        if task:
            command = "rsync -R %(source)s" % task
            if self.verbose:
                print(command)
            status, out, err = self.stream.cli.foreground_run(command)
            if status:
                raise AccessError("Return code %r\n%s" % (status, err))
        else:
            out = None
        return out

    def generate_stream_task(self, task=None, out=None):
        if task and out:
            depth = task['location'].count('/')
            if self.public: depth -= 1
            for result in out.split(b"\n"):
                result = result.decode('utf-8')
                if result.startswith(('d', '-', 'l')):
                    try:
                        location = search(r"^.*\s{1,3}(.+)$", result).group(1)
                    except:
                        location = None
                    if location and location.count('/') == depth:
                        source = join(self.stream.source, location) if self.remote_base else None
                        destination = join(self.stream.destination, location)
                        yield (location, source, destination)

    def set_stream_task(self, task=None):
        out = self.get_task_out(task=task)
        stream_has_task = False
        for location, source, destination in self.generate_stream_task(task=task, out=out):
            if location and source and destination:
                stream_has_task = True
                self.stream.append_task(location=location, source=source, destination=destination)
                """if self.verbose:
                    print("SDSS_ACCESS> Preparing to download: %s" % location)
                    print("SDSS_ACCESS> from: %s" % source)
                    print("SDSS_ACCESS> to: %s" % destination)
                    print("-"*80)"""

        if not stream_has_task:
            print('SDSS_ACCESS> Error: stream has nothing to do.')

    def commit(self, offset=None, limit=None, dryrun=False):
        """ Start the rsync download """

        self.stream.command = "rsync -avRK --files-from={path} {source} {destination}"
        self.stream.append_tasks_to_streamlets(offset=offset, limit=limit)
        self.stream.commit_streamlets()
        self.stream.run_streamlets()
        self.stream.reset_streamlet()
