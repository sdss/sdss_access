from __future__ import absolute_import, division, print_function, unicode_literals
# The line above will help with 2to3 support.

from os.path import isfile, exists, dirname, join, basename, getsize, sep
from re import search
from sdss_access import SDSSPath, AccessError
from sdss_access.sync.auth import Auth
from sdss_access.sync.stream import Stream
from urllib.request import urlopen, urlencode
import re
from platform import system
from os import makedirs

class CurlAccess(SDSSPath):
    """Class for providing Curl access to SDSS SAS Paths
    """

    def __init__(self, label='sdss_curl', stream_count=5, mirror=False, public=False, release=None, verbose=False):
        super(CurlAccess, self).__init__(mirror=mirror, public=public, release=release, verbose=verbose)
        self.label = label
        self.auth = None
        self.stream = None
        self.stream_count = stream_count
        self.verbose = verbose
        print('-----curl.py--init--label',self.label,'stream_count',self.stream_count,'verbose',verbose,'setting initial stream')
        self.initial_stream = self.get_stream()
        print('self.initial_stream',self.initial_stream)

    def get_stream(self):
        stream = Stream(stream_count=self.stream_count, verbose=self.verbose)
        return stream

    def remote(self, username=None, password=None, inquire=None):
        """ Configures remote access """

        self.set_netloc(sdss=True)  # simplifies things to have a single sdss machine in .netrc
        self.set_auth(username=username, password=password, inquire=inquire)
        #self.set_netloc(dtn=not self.public)
        self.set_remote_base(scheme="https")
        print('---curl--remote--self.remote_base', self.remote_base)

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

    def add(self, filetype, **kwargs):
        """ Adds a filepath into the list of tasks to download"""
        print('----curl--add')
        location = self.location(filetype, **kwargs)
        source = self.url(filetype, sasdir='sas', **kwargs)
        if 'full' not in kwargs:
            destination = self.full(filetype, **kwargs)
        else:
            destination = kwargs.get('full')
        print('---curl--destination',destination)

        if location and source and destination:
            self.initial_stream.append_task(location=location, source=source, destination=destination)
            print('----curl---added to initial_stream')
        else:
            print("There is no file with filetype=%r to access in the tree module loaded" % filetype)

    def set_stream(self):
        """ Sets the download streams """

        if not self.auth:
            raise AccessError("Please use the remote() method to set curl authorization or use remote(public=True) for public data")
        elif not self.initial_stream.task:
            raise AccessError("No files to download.")
        else:
            self.stream = self.get_stream()
            self.stream.source = join(self.remote_base, 'sas')
            if 'win' in system().lower(): self.stream.source = self.stream.source.replace(sep,'/')
            self.stream.destination = self.base_dir
            print('-----curl---stream source', self.stream.source,'stream destination', self.stream.destination)
            self.stream.cli.env = {'CURL_PASSWORD': self.auth.password} if self.auth.ready() else None
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
            if self.public:
                command = "curl -I %s --fail" % ['source']
            else:
                command = "curl %s-I %s --fail" % (('-u %s:%s '%(self.auth.username, self.auth.password)) if self.auth.username and self.auth.password else '', task['source'])
            print('---curl---command', command)
            if self.verbose:
                print(command)
            status, out, err = self.stream.cli.foreground_run(command)
            if status:
                raise AccessError("Return code %r\n%s" % (status, err))
        else:
            out = None
        print('---curl curl -I command', status, out, err)
        return status, out

    def generate_stream_task(self, task=None):
        if task:
            location = task['location']
            query_string = basename(location).replace('*','.*') if basename(location) else '.*'
            directory = dirname(location)
            url_directory = join(self.stream.source, directory,'')
            if 'win' in system().lower(): url_directory = url_directory.replace(sep,'/')
            print('---curl---url', url_directory)
            if not self.public and self.auth.username and self.auth.password:
                urlencode({ 'username': self.auth.username,'password': self.auth.password}) 
            for file_size, file_date, filename in re.findall(r'<td>          (\d*)</td><td>(.*)</td></tr>\r\n<tr><td><a.*title="(%s)">'%query_string, urlopen(url_directory).read().decode('utf-8')):
                location = join(directory, filename)
                source = join(self.stream.source, location) if self.remote_base else None
                if 'win' in system().lower(): source = source.replace(sep,'/')
                destination = join(self.stream.destination, location)
                print('----curl---filename', filename, 'location',location, 'source', source, 'destination', destination)
                '''Below was an attempt to see if an existing in directory file was identical to the minute.
                    However, the times of the downloaded file differs by a few hours, the size is largely different.
                    I suspect the database time and size stamps vary from downloaded, since I tried with a second method as well.
                #Online vs local file check to see if needs updating (time difference only accurate to the minute)
                if exists(destination) and getsize(destination) == int(file_size) and abs(datetime.strptime(file_date, "%Y-%b-%d %H:%M") - datetime.fromtimestamp(getmtime(destination))).minutes == 0: print('Already Downloaded at %s'%destination)
                else:'''
                yield (location, source, destination)

    def set_stream_task(self, task=None):
        status, out = self.get_task_out(task=task)
        stream_has_task = False
        if status == 0:
            for location, source, destination in self.generate_stream_task(task=task):
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

    def refine_task(self, regex=None):
        self.stream.refine_task(regex=regex)

    def commit(self, offset=None, limit=None, dryrun=False):
        """ Start the curl download """
        if self.public:
            self.stream.command = "cd {destination} && xargs -n1 curl %s-ORL < {path} --create-dirs --fail"
        else:
            self.stream.command = "cd {destination} && xargs -n1 curl %s-ORL < {path} --create-dirs --fail" % (('-u %s:%s '%('username', 'password')) if True and True else '')
        self.stream.append_tasks_to_streamlets(offset=offset, limit=limit)
        self.stream.commit_streamlets()
        self.stream.run_streamlets()
        self.stream.reset_streamlet()
