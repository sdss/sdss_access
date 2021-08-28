from __future__ import absolute_import, division, print_function, unicode_literals
# The line above will help with 2to3 support.

import distutils.spawn
import re
import time
from os import popen
from os.path import exists, dirname, join, basename, getsize, getmtime, sep
from datetime import datetime, timedelta
from sdss_access import AccessError
from sdss_access.sync.baseaccess import BaseAccess
from sdss_access import is_posix

try:
    from urllib2 import (HTTPPasswordMgrWithDefaultRealm, HTTPBasicAuthHandler, build_opener,
                         install_opener, urlopen)
except Exception:
    from urllib.request import (HTTPPasswordMgrWithDefaultRealm, HTTPBasicAuthHandler, build_opener,
                                install_opener, urlopen)


class CurlAccess(BaseAccess):
    """Class for providing Curl access to SDSS SAS Paths
    """
    remote_scheme = 'https'
    access_mode = 'curl'

    def __init__(self, label='sdss_curl', stream_count=5, mirror=False, public=False, release=None,
                 verbose=False):

        if not distutils.spawn.find_executable('curl'):
            msg = ('cURL does not appear to be installed. To install, the cURL '
                   'download wizard is located at: https://curl.haxx.se/dlwiz/. '
                   'Installation tutorials for cURL (software from https://curl.haxx.se) '
                   'are available online.')
            raise AccessError(msg)

        super(CurlAccess, self).__init__(stream_count=stream_count, mirror=mirror, public=public,
                                         release=release, verbose=verbose, label=label)

    def __repr__(self):
        return '<CurlAccess(using="{0}")>'.format(self.netloc)

    def get_task_status(self, task=None):
        if task:
            try:
                self.set_url_list(task['source'])
                is_there_any_files = len(self.file_line_list) > 0
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
        password_mgr = HTTPPasswordMgrWithDefaultRealm()
        password_mgr.add_password(None, url_directory, self.auth.username, self.auth.password)
        handler = HTTPBasicAuthHandler(password_mgr)
        opener = build_opener(handler)
        opener.open(url_directory)
        install_opener(opener)

    def get_query_list(self, url_query):
        """Search through user specified "*" options and return all possible and valid url paths"""

        # Find query locations and set a descriptive dictionary
        query_objects = [{'segment_number': index, 'query_directory': '', 'query_list_index': 0,
                          'query_list': [], 'query': query.replace('*', '.*')} for index, query in
                         enumerate(url_query.split('/')) if '*' in query or index == len(url_query.split('/')) - 1]

        # Set quick use observables of query_objects
        segment_numbers = [query_object['segment_number'] for query_object in query_objects]
        max_depth = len(query_objects) - 1

        # Set url array used to append user specified urls
        query_results = []

        # Walk and search through optional branches for potential urls that pass user specifications
        query_depth = None

        if self.verbose:
            print("SDSS_ACCESS> Expanding wildcards %r" % url_query)

        while query_depth != 0:
            if query_depth is None:
                query_depth = 0

            # Set branch directory
            query_objects[query_depth]['query_directory'] = ''
            for segment_index, segment in enumerate(url_query.split('/')[:query_objects[query_depth]['segment_number']]):
                if segment_index not in segment_numbers:
                    query_objects[query_depth]['query_directory'] = '/'.join([query_objects[query_depth]['query_directory'], segment] if query_objects[query_depth]['query_directory'] else [segment])
                else:
                    query_object = query_objects[segment_numbers.index(segment_index)]
                    query_branch = query_object['query_list'][query_object['query_list_index']]
                    query_objects[query_depth]['query_directory'] = '/'.join([query_objects[query_depth]['query_directory'], query_branch])

            # Get user specified url options at branch directory
            try:
                query_objects[query_depth]['query_list'] = [item.split('"')[0] for item in re.findall(r'<a href="(%s)%s".*</a></td><td>'%(query_objects[query_depth]['query'], '/' if query_depth != max_depth else ''), urlopen(query_objects[query_depth]['query_directory']).read().decode('utf-8').replace('<tr><td><a href="../">Parent directory/</a></td><td>-</td><td>-</td></tr>', ''))]
            except Exception as e:
                query_objects[query_depth]['query_list'] = []
                if 'Unauthorized' in e:
                    raise AccessError("Return code %r\n" % e)

            # Append full url's that fit user specifications
            if query_depth == max_depth and len(query_objects[query_depth]['query_list']):
                for item in query_objects[query_depth]['query_list']:
                    query_results.append('/'.join([query_objects[query_depth]['query_directory'], item]))

            # Specify walker logic to recognize when to step down the branch or back up and go to the next option
            if not len(query_objects[query_depth]['query_list']) or query_depth == max_depth:
                query_depth -= 1
                while query_depth > -1 and query_objects[query_depth]['query_list_index'] == len(query_objects[query_depth]['query_list'])-1:
                    query_objects[query_depth]['query_list_index'] = 0
                    query_depth -= 1
                query_objects[query_depth]['query_list_index'] += 1
                query_depth += 1
            else:
                query_depth += 1

        return query_results

    def set_url_list(self, query_path=None):
        """Gets url paths from get_query_list and returns file proparties and path"""
        if not is_posix:
            query_path = query_path.replace(sep, '/')
        if not self.public:
            self.set_url_password(query_path)

        self.file_line_list, self.file_size_list, self.file_date_list, self.url_list = [], [], [], []
        for url in self.get_query_list(query_path):
            file_line, file_size, file_date = re.findall(r'<a href="(%s)".*</a></td><td>\s*(\d*)</td><td>(.*)</td></tr>\r' % basename(url), urlopen(dirname(url)).read().decode('utf-8'))[0]
            self.url_list.append(url)
            self.file_line_list.append(file_line.split('"')[0])
            self.file_size_list.append(file_size)
            self.file_date_list.append(file_date)

    def generate_stream_task(self, task=None, out=None):
        ''' creates the task to put in the download stream '''
        if task:
            location = task['location']
            for filename, file_size, file_date, url in zip(self.file_line_list, self.file_size_list, self.file_date_list, self.url_list):
                location = url.split('/sas/')[-1]
                source = join(self.stream.source, location) if self.remote_base else None
                destination = join(self.stream.destination, location)
                if not is_posix:
                    source = source.replace(sep, '/')
                    destination = destination.replace('/', sep)
                    location = location.replace('/', sep)
                if not self.check_file_exists_locally(destination, file_size, file_date):
                    yield (location, source, destination)

    def check_file_exists_locally(self, destination=None, url_file_size=None, url_file_time=None):
        """Checks if file already exists (note that time check is only accurate to the minute)"""
        if exists(destination):
            existing_file_size = int(popen('gzip -l %s' % destination).readlines()[1].split()[0]) if '.gz' in destination else getsize(destination)
            url_file_time = datetime.strptime(url_file_time, "%Y-%b-%d %H:%M" if len(url_file_time.split('-')[0]) == 4 else "%d-%b-%Y %H:%M")
            local_file_time = datetime.utcfromtimestamp(getmtime(destination))
            url_file_time = url_file_time + timedelta(seconds=time.altzone if time.daylight else time.timezone)
            if existing_file_size == int(url_file_size) and abs(url_file_time - local_file_time).seconds < 60:
                print('Already Downloaded at %s' % destination)
                return True
            else:
                return False
        else:
            return False

    def set_stream_task(self, task=None):
        status = self.get_task_status(task=task)
        if status:
            super(CurlAccess, self).set_stream_task(task=task)

    def _get_sas_module(self):
        ''' gets the sas module used when committing the download '''
        return "sas"

    def _get_stream_command(self):
        ''' gets the stream command used when committing the download '''
        auth = ''
        if self.auth.username and self.auth.password:
            auth = '-u {0}:{1}'.format(self.auth.username, self.auth.password)
        return "curl {0} --create-dirs --fail -sSRLK {{path}}".format(auth)
