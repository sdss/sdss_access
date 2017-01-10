from __future__ import division, print_function

import os
import re
from glob import glob
from os.path import join
from random import choice, sample
from re import compile

try:
    from ConfigParser import RawConfigParser
except ImportError:
    from configparser import RawConfigParser

"""
Module for constructing paths to SDSS files.

Example use case:

    from sdss_access.path import Path
    sdss_path = Path()
    filename = sdss_path.full('photoObj', run=94, rerun='301', camcol=1, field=100)

Depends on the tree product. In particular requires path templates in:
  $TREE_DIR/data/sdss_paths.ini
"""


class BasePath(object):
    """Class for construction of paths in general.

    Attributes
    ----------
    templates : dict
        The set of templates read from the configuration file.
    """

    _netloc = {"dtn":"sdss@dtn01.sdss.org", "sdss":"data.sdss.org", "mirror":"data.mirror.sdss.org"}

    def __init__(self, pathfile, mirror=False, public=False, verbose=False):
        self.mirror = mirror
        self.public = public
        self.verbose = verbose
        self.set_netloc()
        self.set_remote_base()
        self._pathfile = pathfile
        self._config = RawConfigParser()
        self._config.optionxform = str
        self.templates = dict()
        self._input_templates()
        return

    def _input_templates(self):
        """Read the path template file.
        """
        foo = self._config.read([self._pathfile])
        if len(foo) == 1:
            for k, v in self._config.items('paths'):
                self.templates[k] = v
        else:
            raise ValueError("Could not read {0}!".format(self._pathfile))
        return

    def dir(self, filetype, **kwargs):
        """Return the directory containing a file of a given type.

        Parameters
        ----------
        filetype : str
            File type parameter.

        Returns
        -------
        dir : str
            Directory containing the file.
        """
        full = kwargs.get('full', self.full(filetype, **kwargs))
        return os.path.dirname(full)

    def name(self, filetype, **kwargs):
        """Return the directory containing a file of a given type.

        Parameters
        ----------
        filetype : str
            File type parameter.

        Returns
        -------
        name : str
            Name of a file with no directory information.
        """
        full = kwargs.get('full', self.full(filetype, **kwargs))
        return os.path.basename(full)

    def exists(self, filetype, **kwargs):
        '''Checks if the given type of file exists

        Parameters
        ----------
        filetype : str
            File type parameter.

        Returns
        -------
        exists : bool
            Boolean indicating if the file exists on disk.

        '''
        full = kwargs.get('full', self.full(filetype, **kwargs))
        return os.path.isfile(full)

    def expand(self, filetype, **kwargs):
        ''' Expand a wildcard path locally

        Parameters
        ----------
        filetype : str
            File type parameter.

        as_url: bool
            Boolean to return SAS urls

        refine: str
            Regular expression string to filter the list of files by
            before random selection

        Returns
        -------
        expand : list
            List of expanded full paths of the given type.

        '''
        full = kwargs.get('full', self.full(filetype, **kwargs))
        assert '*' in full, 'Wildcard must be present in full path'
        files = glob(full)

        # return as urls?
        as_url = kwargs.get('as_url', None)
        newfiles = [self.url('', full=full) for full in files] if as_url else files

        # optionally refine the results
        refine = kwargs.get('refine', None)
        if refine:
            newfiles = self.refine(newfiles, refine, **kwargs)

        return newfiles

    def any(self, filetype, **kwargs):
        ''' Checks if the local directory contains any of the type of file

        Parameters
        ----------
        filetype : str
            File type parameter.

        Returns
        -------
        any : bool
            Boolean indicating if the any files exist in the expanded path on disk.

        '''
        expanded_files = self.expand(filetype, **kwargs)
        return any(expanded_files)

    def one(self, filetype, **kwargs):
        ''' Returns random one of the given type of file

        Parameters
        ----------
        filetype : str
            File type parameter.

        as_url: bool
            Boolean to return SAS urls

        refine: str
            Regular expression string to filter the list of files by
            before random selection

        Returns
        -------
        one : str
            Random file selected from the expanded list of full paths on disk.

        '''
        expanded_files = self.expand(filetype, **kwargs)
        isany = self.any(filetype, **kwargs)
        return choice(expanded_files) if isany else None

    def random(self, filetype, **kwargs):
        ''' Returns random number of the given type of file

        Parameters
        ----------
        filetype : str
            File type parameter.

        num : int
            The number of files to return

        as_url: bool
            Boolean to return SAS urls

        refine: str
            Regular expression string to filter the list of files by
            before random selection

        Returns
        -------
        random : list
            Random file selected from the expanded list of full paths on disk.

        '''
        expanded_files = self.expand(filetype, **kwargs)
        isany = self.any(filetype, **kwargs)
        if isany:
            # get the desired number
            num = kwargs.get('num', 1)
            assert num <= len(expanded_files), 'Requested number must be larger the sample.  Reduce your number.'
            return sample(expanded_files, num)
        else:
            return None

    def refine(self, filelist, regex, filterdir='out', **kwargs):
        ''' Returns a list of files filterd by a regular expression

        Parameters
        ----------
        filelist : list
            A list of files to filter on.

        regex : str
            The regular expression string to filter your list

        filterdir: {'in', 'out'}
            Indicates the filter to be inclusive or exclusive
            'out' removes the items satisfying the regular expression
            'in' keeps the items satisfying the regular expression

        Returns
        -------
        refine : list
            A file list refined by an input regular expression.

        '''
        assert filelist, 'Must provide a list of filenames to refine on'
        assert regex, 'Must provide a regular expression to refine the file list'
        r = compile(regex)

        # icheck filter direction; default is out
        assert filterdir in ['in', 'out'], 'Filter direction must be either "in" or "out"'
        if filterdir == 'out':
            subset = list(filter(lambda i: r.search(i), filelist))
        elif filterdir == 'in':
            subset = list(filter(lambda i: not r.search(i), filelist))
        return subset

    def full(self, filetype, **kwargs):
        """Return the full name of a given type of file.

        Parameters
        ----------
        filetype : str
            File type parameter.

        Returns
        -------
        full : str
            The full path to the file.
        """
        try:
            template = self.templates[filetype]
        except KeyError:
            return None
        # Now replace {} items
        template = template.format(**kwargs)

        # Now replace environmental variables
        envvars = re.findall(r"\$\w+", template)
        for envvar in envvars:
            try:
                value = os.environ[envvar[1:]]
            except KeyError:
                return None
            template = re.sub("\\" + envvar, value, template)

        # Now call special functions as appropriate
        functions = re.findall(r"\%\w+", template)
        for function in functions:
            try:
                method = getattr(self, function[1:])
            except AttributeError:
                return None
            value = method(filetype, **kwargs)
            template = re.sub(function, value, template)

        return template

    def set_netloc(self, netloc=None, sdss=None, dtn=None):
        self.netloc =  netloc if netloc else self._netloc["sdss"] if sdss else self._netloc["dtn"] if dtn  else self._netloc["mirror"] if self.mirror else self._netloc["sdss"]

    def set_remote_base(self, scheme=None):
        self.remote_base = self.get_remote_base(scheme=scheme) if scheme else self.get_remote_base()

    def get_remote_base(self, scheme="https"):
        return "{scheme}://{netloc}".format(scheme=scheme, netloc=self.netloc)

    def set_base_dir(self, base_dir=None):

        if base_dir:
            self.base_dir = base_dir
        else:
            try:
                self.base_dir = join(os.environ['SAS_BASE_DIR'], '')
            except:
                pass

    def location(self, filetype, base_dir=None, **kwargs):
        """Return the location of the relative sas path of a given type of file.

        Parameters
        ----------
        filetype : str
            File type parameter.

        Returns
        -------
        full : str
            The relative sas path to the file.
        """

        full = kwargs.get('full', self.full(filetype, **kwargs))

        self.set_base_dir(base_dir=base_dir)
        location = full[len(self.base_dir):] if full and full.startswith(self.base_dir) else None

        if '//' in location:
            location = location.replace('//', '/')

        return location

    def url(self, filetype, base_dir=None, sasdir='sas', **kwargs):
        """Return the url of a given type of file.

        Parameters
        ----------
        filetype : str
            File type parameter.

        Returns
        -------
        full : str
            The sas url to the file.
        """

        location = self.location(filetype, **kwargs)
        return join(self.remote_base, sasdir, location) if self.remote_base and location else None


class Path(BasePath):
    """Derived class.  Sets a particular template file.
    """
    def __init__(self, mirror=False, public=False, verbose=False):
        try: tree_dir = os.environ['TREE_DIR']
        except KeyError:
            raise NameError("Could not find TREE_DIR in the environment!  Did you load the tree product?")
        pathfile = os.path.join(tree_dir, 'data', 'sdss_paths.ini')

        super(Path, self).__init__(pathfile, mirror=mirror, public=public, verbose=verbose)

    def plateid6(self, filetype, **kwargs):
        """Print plate ID, accounting for 5-6 digit plate IDs.

        Parameters
        ----------
        filetype : str
            File type parameter.
        plateid : int or str
            Plate ID number.  Will be converted to int internally.

        Returns
        -------
        plateid6 : str
            Plate ID formatted to a string of 6 characters.
        """
        plateid = int(kwargs['plateid'])
        if plateid < 10000:
            return "{:0>6d}".format(plateid)
        else:
            return "{:d}".format(plateid)

    def platedir(self, filetype, **kwargs):
        """Returns plate subdirectory in :envvar:`PLATELIST_DIR` of the form: ``NNNNXX/NNNNNN``.

        Parameters
        ----------
        filetype : str
            File type parameter.
        plateid : int or str
            Plate ID number.  Will be converted to int internally.

        Returns
        -------
        platedir : str
            Plate directory in the format ``NNNNXX/NNNNNN``.
        """
        plateid = int(kwargs['plateid'])
        plateid100 = plateid // 100
        subdir = "{:0>4d}".format(plateid100) + "XX"
        return os.path.join(subdir, "{:0>6d}".format(plateid))

    def spectrodir(self, filetype, **kwargs):
        """Returns :envvar:`SPECTRO_REDUX` or :envvar:`BOSS_SPECTRO_REDUX`
        depending on the value of `run2d`.

        Parameters
        ----------
        filetype : str
            File type parameter.
        run2d : int or str
            2D Reduction ID.

        Returns
        -------
        spectrodir : str
            Value of the appropriate environment variable.
        """
        if str(kwargs['run2d']) in ('26', '103', '104'):
            return os.environ['SPECTRO_REDUX']
        else:
            return os.environ['BOSS_SPECTRO_REDUX']


class AccessError(Exception):
    pass
