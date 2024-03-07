from __future__ import absolute_import, division, print_function, unicode_literals
# The line above will help with 2to3 support.

import abc
import six
from os.path import join, sep
from sdss_access import Path
from sdss_access.sync.auth import Auth, AuthMixin
from sdss_access.sync.stream import Stream
from sdss_access import is_posix, AccessError


class BaseAccess(six.with_metaclass(abc.ABCMeta, AuthMixin, Path)):
    """Class for providing Rsync or Curl access to SDSS SAS Paths
    """
    remote_scheme = None
    access_mode = 'rsync' if is_posix else 'curl'

    def __init__(self, label=None, stream_count=5, mirror=False, public=False, release=None,
                 verbose=False, force_modules=None, preserve_envvars=None):
        super(BaseAccess, self).__init__(release=release, public=public,
                                         mirror=mirror, verbose=verbose,
                                         force_modules=force_modules,
                                         preserve_envvars=preserve_envvars)
        self.label = label
        self.auth = None
        self.stream = None
        self.stream_count = stream_count
        self._stream_command = None
        self.verbose = verbose
        self.initial_stream = self.get_stream()

    def remote(self, username=None, password=None, inquire=None):
        """ Configures remote access """
        use_dtn = self.remote_scheme == 'rsync'
        # simplifies things to have a single sdss (or sdss5) machine in
        # .netrc for SDSS-IV  (or SDSS-V, respectively).
        sdss5 = self.is_sdss5()
        # set sdss5 true if s5cfg (e.g. sdsswork or ipl-N) starts with
        # values defined in self._s5cfgs (e.g. sdss or ipl).
        self.set_netloc(sdss=not sdss5, sdss5=sdss5)
        self.set_auth(username=username, password=password, inquire=inquire)
        if use_dtn:
            self.set_netloc(dtn=use_dtn)
        self.set_remote_base(scheme=self.remote_scheme)

    def add(self, filetype, **kwargs):
        """ Adds a filepath into the list of tasks to download"""

        location = self.location(filetype, **kwargs)
        sas_module, location = location.split(sep, 1) if location else (None, location)

        # set proper sasdir based on access method
        sasdir = 'sas' if self.access_mode == 'curl' else ''
        source = self.url(filetype, sasdir=sasdir, **kwargs)

        # raise error if attempting to add a software product path
        if 'svn.sdss.org' in source:
            raise AccessError('Rsync/Curl Access not allowed for svn paths.  Please use HttpAccess.')

        if 'full' not in kwargs:
            destination = self.full(filetype, **kwargs)
        else:
            destination = kwargs.get('full')

        if sas_module and location and source and destination:
            self.initial_stream.append_task(
                sas_module=sas_module, location=location, source=source, destination=destination)
        else:
            print("There is no file with filetype=%r to access in the tree module loaded" % filetype)

    def add_file(self, path, input_type = None):
        """ Adds a file into the list of tasks to download

        Adds a full filepath, url, or location to the list of tasks to
        download.  This takes advantage of ``sdss_access`` parallel streams
        to download a list of files.

        This is similar to the  ``.add`` method, except this takes
        full filepaths or urls as input, whereas the ``.add`` method
        is better when inputing a product name and path template kwargs.

        Parameters
        ----------
        path : str
            the filepath, url, or location
        input_type : str, optional
            the type of input, by default None
        """

        # check for input_type if none provided
        if not input_type:
            if path.startswith(('rsync', 'http')):
                input_type = 'url'
            elif path.startswith('/'):
                input_type = 'filepath'
            else:
                input_type = 'location'

        # use the right sasdir based on mode
        sasdir = 'sas' if self.access_mode == 'curl' else ''

        # determine stream task info
        if input_type == 'filepath':
            location = self.location('', full=path)
            sas_module, location = location.split(sep, 1) if location else (None, location)
            source = self.url('', sasdir=sasdir, full=path)
            dest = path
        elif input_type == 'url':
            self.set_base_dir()
            dest = path.replace(f'{self.remote_base}/{sasdir}', self.base_dir)
            source = path
            location = self.location('', full=dest)
            sas_module, location = location.split(sep, 1) if location else (None, location)
        elif input_type == 'location':
            sas_module, location = path.split(sep, 1) if path else (None, path)
            dest = join(self.base_dir, path)
            source = self.url('', sasdir=sasdir, full=dest)

        # append the task to the stream
        self.initial_stream.append_task(sas_module=sas_module, location=location,
                                        source=source, destination=dest)

    def set_stream(self):
        """ Sets the download streams """

        if not self.auth:
            raise AccessError(
                "Please use the remote() method to set rsync authorization or use remote(public=True) for public data")
        elif not self.initial_stream.task:
            raise AccessError("No files to download.")
        else:
            self.stream = self.get_stream()

            # set stream source based on access mode
            if self.access_mode == 'rsync':
                self.stream.source = self.remote_base
            elif self.access_mode == 'curl':
                self.stream.source = join(self.remote_base, 'sas').replace(sep, '/')

            # set stream destination
            self.stream.destination = self.base_dir

            # set client env dict based on access mode
            if self.access_mode == 'rsync':
                key = 'RSYNC_PASSWORD'
            elif self.access_mode == 'curl':
                key = 'CURL_PASSWORD'
            self.stream.cli.env = {key: self.auth.password} if self.auth.ready() else None

            if self.stream.source and self.stream.destination:
                for task in self.initial_stream.task:
                    self.set_stream_task(task)
            ntask = len(self.stream.task)
            if self.stream.stream_count > ntask:
                if self.verbose:
                    print("SDSS_ACCESS> Reducing the number of streams from %r to %r, the number of download tasks." % (
                        self.stream.stream_count, ntask))
                self.stream.stream_count = ntask
                self.stream.streamlet = self.stream.streamlet[:ntask]

    def get_stream(self):
        ''' return a Stream object '''
        stream = Stream(stream_count=self.stream_count, verbose=self.verbose)
        return stream

    def reset(self):
        ''' Reset all streams '''

        # reset the main stream
        if self.stream:
            self.stream.reset()

        # reset the initial stream (otherwise old 'adds' remain in the new stream)
        if self.initial_stream:
            self.initial_stream.reset()

    def shuffle(self):
        ''' Shuffle the stream '''
        self.stream.shuffle()

    def get_locations(self, offset=None, limit=None):
        ''' Rreturn the locations for all paths in the stream '''
        return self.stream.get_locations(offset=offset, limit=limit) if self.stream else None

    def get_paths(self, offset=None, limit=None):
        ''' Return the base paths for all paths in the stream '''
        locations = self.get_locations(offset=offset, limit=limit)
        sasdir = self._get_sas_module()
        paths = [join(self.base_dir, sasdir, location) for location in locations] if locations else None
        return paths

    def get_urls(self, offset=None, limit=None):
        ''' Return the urls for all paths in the stream '''
        locations = self.get_locations(offset=offset, limit=limit)
        remote_base = self.get_remote_base()
        sasdir = self._get_sas_module()
        urls = [join(remote_base, sasdir, location) for location in locations] if locations else None
        return urls

    @abc.abstractmethod
    def generate_stream_task(self, task=None, out=None):
        ''' creates the task to put in the download stream '''

    def set_stream_task(self, task=None, out=None):
        ''' sets the path input dictionary for a task in a stream '''
        stream_has_task = False
        for sas_module, location, source, destination in self.generate_stream_task(task=task, out=out):
            if sas_module and location and source and destination:
                stream_has_task = True
                self.stream.append_task(sas_module=sas_module, location=location, source=source,
                                        destination=destination)
                """if self.verbose:
                    print("SDSS_ACCESS> Preparing to download: %s" % join(sas_module, location))
                    print("SDSS_ACCESS> from: %s" % source)
                    print("SDSS_ACCESS> to: %s" % destination)
                    print("-"*80)"""

        if not stream_has_task:
            print('SDSS_ACCESS> Error: stream has nothing to do.')

    @abc.abstractmethod
    def _get_stream_command(self):
        ''' gets the stream command used when committing the download '''

    def commit(self, offset=None, limit=None, follow_symlinks: bool = True):
        """ Start the download """

        self.stream.command = self._get_stream_command(follow_symlinks=follow_symlinks)
        self.stream.sas_module = self._get_sas_module()
        self.stream.append_tasks_to_streamlets(offset=offset, limit=limit)
        self.stream.commit_streamlets()
        self.stream.run_streamlets()
        self.stream.reset_streamlet()
