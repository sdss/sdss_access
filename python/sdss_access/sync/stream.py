from __future__ import absolute_import, division, print_function, unicode_literals
# The line above will help with 2to3 support.

import re
from sdss_access.sync import Cli
from random import shuffle
from os.path import sep, join
from sdss_access import is_posix


class Stream(object):

    max_stream_count = 5

    def __init__(self, stream_count=None, verbose=False):
        self.verbose = verbose
        try:
            self.stream_count = min(int(stream_count), self.max_stream_count)
        except Exception:
            self.stream_count = 0
        self.streamlet = [{'index': index, 'location': None, 'source': None, 'destination': None} for index in range(0, self.stream_count)]
        self.reset()
        self.index = 0
        self.command = None
        self.env = None
        self.source = None
        self.destination = None
        self.cli = Cli(verbose=verbose)

    def reset(self):
        self.reset_task()
        self.reset_streamlet()

    def reset_task(self):
        self.task = []

    def reset_streamlet(self):
        for index in range(0, self.stream_count):
            self.set_streamlet(index=index, location=[], source=[], destination=[])

    def set_streamlet(self, index=None, location=None, source=None, destination=None):
        streamlet = self.get_streamlet(index=index)
        if streamlet:
            try:
                n = len(location)
                ok = n == len(source) and n == len(destination)
                streamlet['location'], streamlet['source'], streamlet['destination'] = (
                    location, source, destination) if ok else (None, None, None)
            except Exception:
                streamlet['location'], streamlet['source'], streamlet['destination'] = (
                    None, None, None)

    def get_streamlet(self, index=None, increment=1):
        if index is None:
            self.index += increment
            if self.index >= self.stream_count:
                self.index = 0
        else:
            try:
                self.index = int(index)
            except Exception:
                self.index = 0
        try:
            streamlet = self.streamlet[self.index]
        except Exception:
            streamlet = None
        return streamlet

    def get_locations(self, offset=None, limit=None):
        locations = [task['location'] for task in self.task] if self.task else None
        if offset:
            locations = locations[offset:]
        if limit:
            locations = locations[:limit]
        if not is_posix:
            locations = [loc.replace('/', sep) for loc in locations]
        else:
            locations = [loc for loc in locations]
        return locations

    def shuffle(self):
        shuffle(self.task)

    def refine_task(self, regex=None):
        locations = self.get_locations()
        r = re.compile(regex)
        subset = filter(lambda i: r.search(i), locations)
        self.task = [self.task[locations.index(s)] for s in subset]

    def append_task(self, location=None, source=None, destination=None):
        if location and source and destination:
            task = {'location': location, 'source': source, 'destination': destination, 'exists': None}
            self.task.append(task)

    def append_tasks_to_streamlets(self, offset=None, limit=None):
        tasks = []
        ntasks = 0
        for index, task in enumerate(self.task):
            if (offset is None or index >= offset):
                tasks.append(task)
                ntasks += 1
            if limit is not None and ntasks >= limit:
                break
        for task in tasks:
            self.append_streamlet(task=task)

    def append_streamlet(self, index=None, task=None):
        streamlet = self.get_streamlet(index=index)
        if streamlet and task:
            streamlet['location'].append(task['location'])
            streamlet['source'].append(task['source'])
            streamlet['destination'].append(task['destination'])

    def commit_streamlets(self):
        if self.command:
            self.cli.set_dir()
            for streamlet in self.streamlet:
                self.commit_streamlet(streamlet)
            if self.verbose:
                print("SDSS_ACCESS> streamlets added to {dir}".format(dir=self.cli.dir))

    def commit_streamlet(self, streamlet=None):
        if streamlet:
            streamlet['path'] = self.cli.get_path(index=streamlet['index'])
            path_txt = "{0}.txt".format(streamlet['path'])
            streamlet['command'] = self.command.format(path=path_txt, source=self.source, destination=self.destination)

            if 'rsync -' in self.command:
                self.cli.write_lines(path=path_txt, lines=[location for location in streamlet['location']])
            else:
                if not is_posix:
                    self.cli.write_lines(path=path_txt, lines=['url ' + join(self.source, location).replace(sep,'/')+'\n'+'output '+join(self.destination, location) for location in streamlet['location']])
                else:
                    self.cli.write_lines(path=path_txt, lines=['url ' + join(self.source, location)+'\n'+'output '+join(self.destination, location) for location in streamlet['location']])

    def run_streamlets(self):
        for streamlet in self.streamlet:
            streamlet['logfile'] = open("{0}.log".format(streamlet['path']), "w")
            streamlet['errfile'] = open("{0}.err".format(streamlet['path']), "w")
            streamlet['process'] = self.cli.get_background_process(streamlet['command'], logfile=streamlet['logfile'], errfile=streamlet['errfile'])
            if self.verbose:
                print("SDSS_ACCESS> rsync stream %s logging to %s" % (streamlet['index'],streamlet['logfile'].name))

        # get the number of tasks per stream
        tasks_per_stream = [len(streamlet['location']) for streamlet in self.streamlet]
        # submit the stream subprocesses to the background
        self.cli.wait_for_processes(list(streamlet['process'] for streamlet in self.streamlet),
                                    n_tasks=len(self.task), tasks_per_stream=tasks_per_stream)

        if any(self.cli.returncode):
            path = self.streamlet[0]['path'][:-3]
            if self.verbose:
                print("SDSS_ACCESS> return code {returncode}".format(
                    returncode=self.cli.returncode))
            print("SDSS_ACCESS> Failed! See error logs in %s." % (path))
        else:
            print("SDSS_ACCESS> Done!")

        for streamlet in self.streamlet:
            streamlet['logfile'].close()
            streamlet['errfile'].close()
