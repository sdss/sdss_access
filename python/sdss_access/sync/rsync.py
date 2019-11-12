from __future__ import absolute_import, division, print_function, unicode_literals
# The line above will help with 2to3 support.

from os.path import join
from re import search
from sdss_access import AccessError
from sdss_access.sync.baseaccess import BaseAccess


class RsyncAccess(BaseAccess):
    """Class for providing Rsync access to SDSS SAS Paths
    """
    remote_scheme = 'rsync'
    access_mode = 'rsync'

    def __init__(self, label='sdss_rsync', stream_count=5, mirror=False, public=False, release=None, 
                 verbose=False):
        super(RsyncAccess, self).__init__(stream_count=stream_count, mirror=mirror, public=public, 
                                          release=release, verbose=verbose)
        self.label = label
        self.auth = None
        self.stream = None
        self.stream_count = stream_count
        self.verbose = verbose
        self.initial_stream = self.get_stream()

    def __repr__(self):
        return '<RsyncAccess(using="{0}")>'.format(self.netloc)

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
        ''' creates the task to put in the download stream '''
        if task and out:
            depth = task['location'].count('/')
            if self.public:
                depth -= 1
            for result in out.split(b"\n"):
                result = result.decode('utf-8')
                if result.startswith(('d', '-', 'l')):
                    try:
                        location = search(r"^.*\s{1,3}(.+)$", result).group(1)
                    except Exception:
                        location = None
                    if location and location.count('/') == depth:
                        source = join(self.stream.source, location) if self.remote_base else None
                        destination = join(self.stream.destination, location)
                        yield (location, source, destination)

    def set_stream_task(self, task=None):
        out = self.get_task_out(task=task)
        super(RsyncAccess, self).set_stream_task(task=task, out=out)

    def _get_stream_command(self):
        ''' gets the stream command used when committing the download '''
        return "rsync -avRK --files-from={path} {source} {destination}"
