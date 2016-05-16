from sdss_access.sync import Cli
from random import shuffle

class Stream:

    max_stream_count = 5

    def __init__(self, stream_count=None, verbose=False):
        self.verbose = verbose
        try: self.stream_count = min(int(stream_count),self.max_stream_count)
        except: self.stream_count = 0
        self.task = []
        self.streamlet = [{'index':index, 'location':None, 'source':None, 'destination':None}  for index in range(0,self.stream_count)]
        self.index = 0
        self.command = None
        self.env = None
        self.source = None
        self.destination = None
        self.cli = Cli()

    def reset_streamlet(self):
        for index in range(0,self.stream_count): self.set_streamlet(index=index, location=[], source=[], destination=[])

    def set_streamlet(self, index=None, location=None, source=None, destination=None):
        streamlet = self.get_streamlet(index=index)
        if streamlet:
            try:
                n = len(location)
                ok = n == len(source) and n == len(destination)
                streamlet['location'], streamlet['source'], streamlet['destination'] = (location, source, destination) if ok else (None, None, None)
            except:
                streamlet['location'], streamlet['source'], streamlet['destination'] = (None, None, None)


    def get_streamlet(self,index=None,increment=1):
        if index is None:
            self.index += increment
            if self.index >= self.stream_count: self.index = 0
        else:
            try: self.index = int(index)
            except: self.index = 0
        try: streamlet = self.streamlet[self.index]
        except: streamlet = None
        return streamlet

    def get_locations(self, offset=None, limit=None):
        locations = [location for location,source,destination in self.task] if self.task else None
        if offset: locations = locations[offset:]
        if limit: locations = locations[:limit]
        return locations
    
    def shuffle(self): shuffle(self.task)

    """def get_streamlet_locations(self):
        return [streamlet['location'] for streamlet in self.streamlet] if self.streamlet else None"""

    def append_task(self, location=None, source=None, destination=None):
        if location and source and destination: self.task.append((location,source,destination))

    def set_streamlets(self):
        for location,source,destination in self.task: self.append_streamlet(location=location,source=source,destination=destination)
    
    def append_streamlet(self, index=None, location=None, source=None, destination=None):
        streamlet = self.get_streamlet(index=index)
        if streamlet:
            if location and source and destination:
                streamlet['location'].append(location)
                streamlet['source'].append(source)
                streamlet['destination'].append(destination)

    def commit_streamlets(self):
        if self.command:
            self.cli.set_dir()
            for streamlet in self.streamlet: self.commit_streamlet(streamlet)
            if self.verbose: print "SDSS_ACCESS> streamlets added to {dir}".format(dir=self.cli.dir)

    def commit_streamlet(self, streamlet=None):
        if streamlet:
            streamlet['path'] = self.cli.get_path(index=streamlet['index'])
            path_txt = "{0}.txt".format(streamlet['path'])
            streamlet['command'] = self.command.format(path=path_txt,source=self.source,destination=self.destination)
            streamlet['env'] = self.env
            self.cli.write_lines(path=path_txt, lines=[location for location in streamlet['location']])

    def run_streamlets(self):
        for streamlet in self.streamlet:
            streamlet['logfile'] = open("{0}.log".format(streamlet['path']),"w")
            streamlet['errfile'] = open("{0}.err".format(streamlet['path']),"w")
            streamlet['process'] = self.cli.get_background_process(streamlet['command'], env=streamlet['env'], logfile=streamlet['logfile'], errfile=streamlet['errfile'])
        self.cli.wait_for_processes(streamlet['process'] for streamlet in self.streamlet)
        print "return code {returncode}".format(returncode=self.cli.returncode)
        for streamlet in self.streamlet: streamlet['logfile'].close()
