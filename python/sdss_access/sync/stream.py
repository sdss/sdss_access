from sdss_access.sync import Cli

class Stream:

    max_stream_count = 5

    def __init__(self, stream_count=None, verbose=False):
        self.verbose = verbose
        try: self.stream_count = min(int(stream_count),self.max_stream_count)
        except: self.stream_count = 0
        self.task = [{'index':index, 'location':None, 'source':None, 'destination':None, 'exists':None}  for index in range(0,self.stream_count)]
        self.index = 0
        self.command = None
        self.env = None
        self.source = None
        self.destination = None
        self.cli = Cli()

    def reset_task(self):
        for index in range(0,self.stream_count): self.set_task(index=index, location=[], source=[], destination=[])

    def set_task(self, index=None, location=None, source=None, destination=None):
        task = self.get_task(index=index)
        if task:
            try:
                n = len(location)
                ok = n == len(source) and n == len(destination)
                task['location'], task['source'], task['destination'] = (location, source, destination) if ok else (None, None, None)
            except:
                task['location'], task['source'], task['destination'] = (None, None, None)


    def get_task(self,index=None,increment=1):
        if index is None:
            self.index += increment
            if self.index >= self.stream_count: self.index = 0
        else:
            try: self.index = int(index)
            except: self.index = 0
        try: task = self.task[self.index]
        except: task = None
        return task

    def get_task_locations(self):
        return [task['location'] for task in self.task] if self.task else None

    def append_task(self, index=None, location=None, source=None, destination=None):
        task = self.get_task(index=index)
        if task:
            if location and source and destination:
                task['location'].append(location)
                task['source'].append(source)
                task['destination'].append(destination)

    def commit_tasks(self):
        if self.command:
            self.cli.set_dir()
            for task in self.task: self.commit_task(task)
            if self.verbose: print "SDSS_ACCESS> tasks added to {dir}".format(dir=self.cli.dir)

    def commit_task(self, task=None):
        if task:
            task['path'] = self.cli.get_path(index=task['index'])
            path_txt = "{0}.txt".format(task['path'])
            task['command'] = self.command.format(path=path_txt,source=self.source,destination=self.destination)
            task['env'] = self.env
            self.cli.write_lines(path=path_txt, lines=[location for location in task['location']])

    def run_tasks(self):
        for task in self.task:
            task['logfile'] = open("{0}.log".format(task['path']),"w")
            task['errfile'] = open("{0}.err".format(task['path']),"w")
            task['process'] = self.cli.get_background_process(task['command'], env=task['env'], logfile=task['logfile'], errfile=task['errfile'])
        self.cli.wait_for_processes(task['process'] for task in self.task)
        print "return code {returncode}".format(returncode=self.cli.returncode)
        for task in self.task: task['logfile'].close()
