import urllib2
from os import makedirs
from os.path import isfile, exists, dirname
from sdss_access import SDSSPath
from sdss_access.sync.auth import Auth

class HttpAccess(SDSSPath):
    """Class for providing HTTP access via urllib2 to SDSS SAS Paths
    """

    def __init__(self, local_base=None, verbose=False):
        super(HttpAccess, self).__init__()
        self.remote_base = 'https://data.sdss.org'
        self.local_base = None
        self.verbose = verbose
        self._remote = False

    def remote(self, remote_base=None, local_base=None, username=None, password=None):
        """
        Configures remote access for NASA-Sloan Atlas.

        Parameters
        ----------
        remote_base : str
            base URL path for remote repository
        local_base : str
            base file path for local repository
        username : str
            user name for remote repository
        password : str
            password for local repository
        """
        if remote_base is not None: self.remote_base = remote_base
        if local_base is not None: self.local_base = local_base
        self._remote = True
        if not username or not password:
            auth = Auth()
            auth.set_host()
            username = auth.username
            password = auth.password
        if username and password:
            passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
            passman.add_password(None, self.remote_base, username, password)
            authhandler = urllib2.HTTPBasicAuthHandler(passman)
            opener = urllib2.build_opener(authhandler)
            urllib2.install_opener(opener)

    def local(self):
        """Configures back to local access
        """
        self._remote = False

    def get(self, filetype, **kwargs):
        """Returns file name, downloading if remote access configured.

        Parameters
        ----------
        filetype : str
            type of file

        keyword arguments :
            keywords to fully specify path

        Notes
        -----
        Path templates are defined in $DIMAGE_DIR/data/dimage_paths.ini
        """
        path = self.full(filetype, **kwargs)
        
        if self._remote: return self.download_url_to_path(self.url(filetype, **kwargs), path)
        return path


    def download_url_to_path(self, url, path, force=False):
        """
        Download a file from url via http, and put it at path

        Parameters
        ----------

        url : str
            URL of file to download

        path : str
            local path to put file in
        """

        path_exists = isfile(path)
        if not path_exists or force:

            dir = dirname(path)
            if not exists(dir):
                if self.verbose: print("CREATE %s" % dir)
                makedirs(dir)

            u = urllib2.urlopen(url)

            with open(path, 'wb') as file:
                meta = u.info()
                meta_func = meta.getheaders \
                    if hasattr(meta, 'getheaders') else meta.get_all
                meta_length = meta_func("Content-Length")
                file_size = None
                if meta_length: file_size = int(meta_length[0])
                if self.verbose: print("Downloading: {0} Bytes: {1}".format(url, file_size))

                file_size_dl = 0
                block_sz = 8192
                while True:
                    buffer = u.read(block_sz)
                    if not buffer: break
                    file_size_dl += len(buffer)
                    file.write(buffer)
    
            if self.verbose:
                if path_exists: print("OVERWRITING %s" % path)
                else: print("CREATE %s" % path)

        elif self.verbose: print("FOUND %s (already downloaded)" % path)

