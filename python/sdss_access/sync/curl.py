from __future__ import absolute_import, division, print_function, unicode_literals
# The line above will help with 2to3 support.

from os.path import isfile, exists, dirname, join, basename, getsize, getmtime, sep
from re import search
from sdss_access import SDSSPath, AccessError
from sdss_access.sync.auth import Auth
from sdss_access.sync.stream import Stream
import urllib
import re
from platform import system
from os import popen
from numpy import transpose
from datetime import datetime

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

    def get_task_status(self, task=None):
        if task:
            try: 
                file_line, file_size, file_date = self.get_url_list(task['source'])
                print('----get_task_status input', task['source'])
                is_there_any_files = len(file_line) > 0
                err = 'Found no files' if not is_there_any_files else ''
            except Exception as e:
                err = e
                is_there_any_files = False
                
            if not is_there_any_files:
                raise AccessError("Return code %r\n" % err)
        else:
            is_there_any_files = False
        return is_there_any_files
        
    def set_url_password(self, url_directory):
        """ Authorize User on sas"""
        url_directory = url_directory.split('sas')[0]
        password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
        password_mgr.add_password(None, url_directory, self.auth.username, self.auth.password)
        handler = urllib.request.HTTPBasicAuthHandler(password_mgr)
        opener = urllib.request.build_opener(handler)
        opener.open(url_directory)
        urllib.request.install_opener(opener)
        
    def get_query_list(self, url_query):
        """Search through user specified "*" options and return all possible and valid urls"""
        
        # Find query locations and set a descriptive dictionary
        query_objects = [{'segment_number':index, 'query_directory':'', 'query_list_index':0, 'query_list':[], 'query':query.replace('*','.*')} for index, query in enumerate(url_query.split('/')) if '*' in query or index == len(url_query.split('/'))-1]
        
        #Set quick use observables of query_objects
        segment_numbers = [query_object['segment_number'] for query_object in query_objects]
        max_depth = len(query_objects)-1
        
        #Set url array used to append user specified urls
        query_results = []

        #Walk and search through option branches for potential urls that pass user specifications
        query_depth = 9999
        while query_depth > 0:
            if query_depth == 9999: query_depth = 0
            
            #Set branch directory
            query_objects[query_depth]['query_directory'] = ''
            for segment_index, segment in enumerate(url_query.split('/')[:query_objects[query_depth]['segment_number']]):
                if segment_index not in segment_numbers:
                    query_objects[query_depth]['query_directory'] = '/'.join([query_objects[query_depth]['query_directory'], segment] if query_objects[query_depth]['query_directory'] else [segment])
                else:
                    query_object = query_objects[segment_numbers.index(segment_index)]
                    query_branch = query_object['query_list'][query_object['query_list_index']]
                    query_objects[query_depth]['query_directory'] = '/'.join([query_objects[query_depth]['query_directory'], query_branch])
            
            #Get user specified url options at branch directory
            try:
                query_objects[query_depth]['query_list'] = [item.split('"')[0] for item in re.findall(r'<a href="(%s)%s".*</a></td><td>'%(query_objects[query_depth]['query'], '/' if query_depth != max_depth else ''), urllib.request.urlopen(query_objects[query_depth]['query_directory']).read().decode('utf-8'))]
            except Exception as e:
                query_objects[query_depth]['query_list'] = []
                if 'Unauthorized' in e:
                    raise AccessError("Return code %r\n" % e)
            
            #Append full url's that fit user specifications
            if query_depth == max_depth and len(query_objects[query_depth]['query_list']):
                for item in query_objects[query_depth]['query_list']:
                    query_results.append('/'.join([query_objects[query_depth]['query_directory'], item]))
                    
            #Specify walker logic to recognize when to step down the branch or back up and go to the next option
            if not len(query_objects[query_depth]['query_list']) or query_depth == max_depth:
                query_depth-=1
                while query_depth > -1 and query_objects[query_depth]['query_list_index'] == len(query_objects[query_depth]['query_list'])-1:
                    query_objects[query_depth]['query_list_index'] = 0
                    query_depth-=1
                query_objects[query_depth]['query_list_index'] += 1
                query_depth+=1
            else:
                query_depth+=1
        return query_results
        
    def get_url_list(self, query_path = None):
        if 'win' in system().lower(): query_path = query_path.replace(sep,'/')
        if not self.public: self.set_url_password(query_path)
        
        file_line_list, file_size_list, file_date_list = [], [], []
        print('---------urls',self.get_query_list(query_path), query_path)
        for url in self.get_query_list(query_path):
            file_line, file_size, file_date = re.findall(r'<a href="(%s)".*</a></td><td>\s*(\d*)</td><td>(.*)</td></tr>\r'%basename(url), urllib.request.urlopen(dirname(url)).read().decode('utf-8'))[0]
            file_line_list.append(file_line.split('"')[0])
            file_size_list.append(file_size)
            file_date_list.append(file_date)       
        return [file_line_list, file_size_list, file_date_list, url]
                
    def generate_stream_task(self, task=None):
        if task:
            location = task['location']
            query_string = basename(location)
            directory = dirname(location)
            url_directory = join(self.stream.source, directory,'')
            print('---curl---url', url_directory)
            print(self.get_url_list('/'.join([url_directory, query_string])))
            for filename, file_size, file_date, url in transpose(self.get_url_list('/'.join([url_directory, query_string]))):
                #location = join(directory, filename)
                location = url.split('/sas/')[-1]
                source = join(self.stream.source, location) if self.remote_base else None
                if 'win' in system().lower(): source = source.replace(sep,'/')
                destination = join(self.stream.destination, location)
                print('----curl---filename', filename, 'location',location, 'source', source, 'destination', destination)
                print('----file_date', file_date)
                if exists(destination):
                    existing_file_size = int(popen('gzip -l %s' % destination).readlines()[1].split()[0]) if '.gz' in destination else getsize(destination)
                    if existing_file_size == int(file_size) and abs(datetime.strptime(file_date, "%Y-%b-%d %H:%M" if len(file_date.split('-')[0]) == 4 else "%d-%b-%Y %H:%M") - datetime.fromtimestamp(getmtime(destination))).seconds < 60: print('Already Downloaded at %s'%destination)
                    else: yield (location, source, destination)
                else: yield (location, source, destination)

    def set_stream_task(self, task=None):
        status = self.get_task_status(task=task)
        stream_has_task = False
        if status:
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
        self.stream.command = "curl %s --create-dirs -RLK {path}" % (('-u %s:%s'%(self.auth.username, self.auth.password)) if self.auth.username and self.auth.password else '')
        self.stream.append_tasks_to_streamlets(offset=offset, limit=limit)
        self.stream.commit_streamlets()
        self.stream.run_streamlets()
        self.stream.reset_streamlet()
