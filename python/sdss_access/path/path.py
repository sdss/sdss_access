from __future__ import division, print_function

import os
import re
import requests
import ast
import inspect
import six
import datetime
from glob import glob
from os.path import join, sep
from random import choice, sample
from sdss_access import tree, log, config
from sdss_access import is_posix

pathlib = None
try:
    import pathlib
except ImportError:
    import pathlib2 as pathlib

# try:
#     from ConfigParser import RawConfigParser
# except ImportError:
#     from configparser import RawConfigParser

"""
Module for constructing paths to SDSS files.

Example use case:

    from sdss_access.path import Path
    sdss_path = Path()
    filename = sdss_path.full('photoObj', run=94, rerun='301', camcol=1, field=100)

Depends on the tree product. In particular requires path templates in:
  $TREE_DIR/data/sdss_paths.ini
"""


def check_public_release(release: str = None, public: bool = False) -> bool:
    """ Check if a release is public

    Checks a given release to see if it is public.  A release is public if it
    contains "DR" in the release name, and if todays date is <= the release_date
    as specified in the Tree.

    Parameters
    ----------
    release : str
        The name of the release to check
    public : bool
        If True, force the release to be public

    Returns
    -------
    bool
        If the release if public

    Raises
    ------
    AttributeError
        when tree does not have a valid release date for a DR tree config
    """
    today = datetime.datetime.now().date()
    release_date = getattr(tree, 'release_date', None)

    # check if tree has a valid release date attr
    if release_date is None and "DR" in tree.release:
        raise AttributeError("Cannot find a valid release date in the sdss-tree product.  Try upgrading to min. version 3.1.0.")

    return ('dr' in release.lower() and release_date <= today) or public


class BasePath(object):
    """Class for construction of paths in general.

    Parameters
    ----------
    release : str
        The release name, e.g. 'DR15', 'MPL-9'.
    public : bool
        If True, uses public urls.  Only needed for public data releases. Automatically set to True
        when release contains "DR".
    mirror : bool
        If True, uses the mirror data domain url.  Default is False.
    verbose : bool
        If True, turns on verbosity.  Default is False.
    force_modules : bool
        If True, forces svn or github software products to use any existing local Module
        environment paths, e.g. PLATEDESIGN_DIR
    preserve_envvars : bool | list
        Flag(s) to indicate some or all original environment variables to preserve

    Attributes
    ----------
    templates : dict
        The set of templates read from the configuration file.
    """

    _netloc = {"dtn": "dtn.sdss.org", "sdss": "data.sdss.org", "sdss5": "data.sdss5.org",
               "mirror": "data.mirror.sdss.org", "svn": "svn.sdss.org"}

    def __init__(self, release=None, public=False, mirror=False, verbose=False,
                 force_modules=None, preserve_envvars=None):
        # set release
        self.release = release or os.getenv('TREE_VER', 'sdsswork')
        self.verbose = verbose
        self.force_modules = force_modules or config.get('force_modules')
        self.preserve_envvars = preserve_envvars or config.get('preserve_envvars')

        # set attributes
        self._special_fxn_pattern = r"\@\w+[|]"
        self._compressions = ['.gz', '.bz2', '.zip']
        self._comp_regex = r'({0})$'.format('|'.join(self._compressions))

        # set the path templates from the tree
        self.templates = tree.paths
        if self.release:
            self.replant_tree(release=self.release)

        # set public and mirror keywords
        self.public = check_public_release(release=self.release, public=public)
        self.mirror = mirror

        # set the server location and remote base
        self.set_netloc()
        self.set_remote_base()

    def __repr__(self):
        return '<BasePath(release="{0}", public={1}, n_paths={2})'.format(self.release.lower(), self.public, len(self.templates))

    def replant_tree(self, release=None):
        ''' Replants the tree based on release

        Resets the path definitions given a specified release

        Parameters
        ----------
            release : str
                A release to use when replanting the tree
        '''
        release = release or self.release
        if release:
            release = release.lower().replace('-', '')
        tree.replant_tree(release, preserve_envvars=self.preserve_envvars)
        self.templates = tree.paths
        self.release = release

    @staticmethod
    def get_available_releases(public=None):
        ''' Get the available releases

        Parameters:
            public (bool):
                If True, only return public data releases
        '''
        return tree.get_available_releases(public=public)

    def lookup_keys(self, name):
        ''' Lookup the keyword arguments needed for a given path name

        Parameters:
            name (str):
                The name of the path

        Returns:
            A list of keywords needed for filepath generation

        '''

        assert name, 'Must specify a path name'
        assert name in self.templates.keys(), '{0} must be defined in the path templates'.format(name)
        # find all words inside brackets
        keys = list(set(re.findall(r'{(.*?)}', self.templates[name])))
        # lookup any keys referenced inside special functions
        skeys = self._check_special_kwargs(name)
        keys.extend(skeys)
        # remove any duplicates
        keys = list(set(keys))
        # remove the type : descriptor
        keys = [k.split(':')[0] for k in keys]
        return keys

    def _check_special_kwargs(self, name):
        ''' check special functions for kwargs

        Checks the content of the special functions (%methodname) for
        any keyword arguments referenced within

        Parameters:
            name (str):
                A path key name

        Returns:
            A list of keyword arguments found in any special functions
        '''
        keys = []
        # find any %method names in the template string
        functions = re.findall(self._special_fxn_pattern, self.templates[name])
        if not functions:
            return keys

        # loop over special method names and extract keywords
        for function in functions:
            method = getattr(self, function[1:-1])
            # get source code of special method
            source = self._find_source(method)
            fkeys = re.findall(r'kwargs\[(.*?)\]', source)
            if fkeys:
                # evaluate to proper string
                fkeys = [ast.literal_eval(k) for k in fkeys]
                keys.extend(fkeys)
        return keys

    @staticmethod
    def _find_source(method):
        ''' find source code of a given method

        Find and extract the source code of a given method in a module.
        Uses inspect.findsource to get all source code and performs some
        selection magic to identify method source code.  Doing it this way
        because inspect.getsource returns wrong method.

        Parameters:
            method (obj):
                A method object

        Returns:
            A string containing the source code of a given method

        Example:
            >>> from sdss_access.path import Path
            >>> path = Path()
            >>> path._find_source(path.full)
        '''

        # get source code lines of entire module method is in
        source = inspect.findsource(method)
        is_method = inspect.ismethod(method)
        # create single source code string
        source_str = '\n'.join(source[0])
        # define search pattern
        if is_method:
            pattern = r'def\s{0}\(self'.format(method.__name__)
        # search for pattern within the string
        start = re.search(pattern, source_str)
        if start:
            # find start and end positions of source code
            startpos = start.start()
            endpos = source_str.find('def ', startpos + 1)
            code = source_str[startpos:endpos]
        else:
            code = None
        return code

    def lookup_names(self):
        ''' Lookup what path names are available

        Returns a list of the available path names in sdss_access.
        Use with lookup_keys to find the required keyword arguments for a
        given path name.

        Returns:
            A list of the available path names.
        '''
        return self.templates.keys()

    def has_name(self, name):
        ''' Check if a given path name exists in the set of templates

        Parameters:
            name (str):
                The path name to lookup
        '''
        assert isinstance(name, six.string_types), 'name must be a string'
        return name in self.lookup_names()

    def extract(self, name, example):
        ''' Extract keywords from an example path

        Attempts to extract the defined keyword values from an example filepath
        for a given path name.  The filepath must be a full SDSS SAS filepath.

        Parameters:
            name (str):
                The name of the path definition
            example (str):
                The absolute filepath to the example file

        Returns:
            A dictionary of path keyword values

        Example:
            >>> from sdss_access.path import Path
            >>> path = Path()
            >>> filepath = '/Users/Brian/Work/sdss/sas/mangawork/manga/spectro/redux/v2_5_3/8485/stack/manga-8485-1901-LOGCUBE.fits'
            >>> path.extract('mangacube', filepath)
            >>> {'drpver': 'v2_5_3', 'plate': '8485', 'ifu': '1901', 'wave': 'LOG'}
        '''

        # if pathlib not available do nothing
        if not pathlib:
            return None

        # ensure example is a string
        if isinstance(example, pathlib.Path):
            example = str(example)
        assert isinstance(example, six.string_types), 'example file must be a string'

        # get the template
        assert name in self.lookup_names(), '{0} must be a valid template name'.format(name)
        template = self.templates[name]

        # expand the environment variable
        template = _expandvars(template)

        # handle special functions; perform a drop in replacement
        if re.match('@spectrodir[|]', template):
            template = re.sub('@spectrodir[|]', os.environ['BOSS_SPECTRO_REDUX'], template)
        elif re.search('@platedir[|]', template):
            template = re.sub('@platedir[|]', r'(.*)/{plateid:0>6}', template)
        elif re.search('@definitiondir[|]', template):
            template = re.sub('@definitiondir[|]', '{designid:0>6}', template)
        elif re.search('@apgprefix[|]', template):
            template = re.sub('@apgprefix[|]', '{prefix}', template)
        elif re.search('@healpixgrp[|]', template):
            template = re.sub('@healpixgrp[|]', '{healpixgrp}', template)
        elif re.search('@configgrp[|]', template):
            template = re.sub('@configgrp[|]', '{configgrp}', template)
        elif re.search('@isplate[|]', template):
            template = re.sub('@isplate[|]', '{isplate}', template)
        elif re.search('@pad_fieldid[|]', template):
           template = re.sub('@pad_fieldid[|]', '{fieldid}', template)
        if re.search('@plateid6[|]', template):
            template = re.sub('@plateid6[|]', '{plateid:0>6}', template)
        if re.search('@component_default[|]', template):
            template = re.sub('@component_default[|]', '{component_default}', template)
        if re.search('@cat_id_groups[|]', template):
            template = re.sub('@cat_id_groups[|]', '{cat_id_groups}', template)

        # check if template has any brackets
        haskwargs = re.search('[{}]', template)
        if not haskwargs:
            return None

        # escape the envvar $ and any dots (use re in case of @platedir sub)
        template = self._remove_compression(template)
        subtemp = template.replace('$', '\\$')
        subtemp = re.sub(r'[.](?!\*)', '\\.', subtemp)
        # define search pattern; replace all template keywords with regex "(.*)" group
        research = re.sub('{(.*?)}', '(.*?)', subtemp)
        research += '$'  # mark the end of a search string (captures cases when {} at end of string)
        # look for matches in template and example
        pmatch = re.search(research, self._remove_compression(template))
        tmatch = re.search(research, self._remove_compression(example))

        path_dict = {}
        # if example match extract keys and values from the match groups
        if tmatch:
            values = tmatch.groups(0)
            keys = pmatch.groups(0)
            assert len(keys) == len(values), 'pattern and template matches must have same length'
            parts = zip(keys, values)
            # parse into dictionary
            for part in parts:
                value = part[1]
                if re.findall('{(.*?)}', part[0]):
                    # get the key name inside the brackets
                    keys = re.findall('{(.*?)}', part[0])
                    # remove the type : designation
                    keys = [k.split(':')[0] for k in keys]
                    # handle double bracket edge cases; remove this when better solution found
                    if len(keys) > 1:
                        if keys[0] == 'dr':
                            # for {dr}{version}
                            drval = re.match('^DR[1-9][0-9]', value).group(0)
                            otherval = value.split(drval)[-1]
                            pdict = {keys[0]: drval, keys[1]: otherval}
                        elif keys[0] in ['rc', 'br', 'filter', 'camrow']:
                            # for {camrow}{camcol}, {filter}{camcol}, {br}{id}, etc
                            pdict = {keys[0]: value[0], keys[1]: value[1:]}
                        else:
                            raise ValueError('This case has not yet been accounted for.')
                        path_dict.update(pdict)
                    else:
                        path_dict[keys[0]] = value
        return path_dict

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

        full = kwargs.get('full', None)
        if not full:
            full = self.full(filetype, **kwargs)

        return os.path.dirname(full)

    def name(self, filetype, **kwargs):
        """Return the name of a file of a given type.

        Parameters
        ----------
        filetype : str
            File type parameter.

        Returns
        -------
        name : str
            Name of a file with no directory information.
        """

        full = kwargs.get('full', None)
        if not full:
            full = self.full(filetype, **kwargs)

        return os.path.basename(full)

    def exists(self, filetype, remote=None, **kwargs):
        '''Checks if the given type of file exists locally

        Parameters
        ----------
        filetype : str
            File type parameter.

        remote : bool
            If True, checks for remote existence of the file

        Returns
        -------
        exists : bool
            Boolean indicating if the file exists.

        '''

        full = kwargs.get('full', None)
        if not full:
            full = self.full(filetype, **kwargs)

        if remote:
            # check for remote existence using a HEAD request
            url = self.url('', full=full)
            verify = kwargs.get('verify', True)
            try:
                resp = requests.head(url, allow_redirects=True, verify=verify)
            except Exception as e:
                raise AccessError('Cannot check for remote file existence for {0}: {1}'.format(url, e))
            else:
                return resp.ok
        else:
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

        full = kwargs.get('full', None)
        if not full:
            full = self.full(filetype, **kwargs)

        # assert '*' in full, 'Wildcard must be present in full path'
        files = glob(self._add_compression_wild(full))

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
        r = re.compile(regex)

        # icheck filter direction; default is out
        assert filterdir in ['in', 'out'], 'Filter direction must be either "in" or "out"'
        if filterdir == 'out':
            subset = list(filter(lambda i: r.search(i), filelist))
        elif filterdir == 'in':
            subset = list(filter(lambda i: not r.search(i), filelist))
        return subset

    def full(self, filetype, **kwargs):
        """Return the full local path of a given type of file.

        Parameters
        ----------
        filetype : str
            File type parameter.
        force_module: bool
            If True, forces software products to use any existing Module environment paths
        kwargs: dict
            Any path template keyword arguments

        Returns
        -------
        full : str
            The full local path to the file.
        """

        # check if full already in kwargs
        if 'full' in kwargs:
            return kwargs.get('full')

        # check for filetype in template
        assert filetype in self.templates, ('No entry {0} found. Filetype must '
                                            'be one of the designated templates '
                                            'in the currently loaded tree'.format(filetype))
        template = self.templates[filetype]
        if not is_posix:
            template = template.replace('/', sep)

        # Check if forcing module paths
        force_module = kwargs.get('force_module', None)
        if force_module or self.force_modules:
            template = self.check_modules(template, permanent=self.force_modules)

        # Now replace {} items
        # check for missing keyword arguments
        keys = self.lookup_keys(filetype)
        # split keys to remove :format from any "key:format"
        keys = [k.split(':')[0] for k in keys]
        missing_keys = set(keys) - set(kwargs.keys())
        if missing_keys:
            raise KeyError('Missing required keyword arguments: {0}'.format(list(missing_keys)))
        else:
            template = template.format(**kwargs)

        # Now replace environmental variables
        template = _expandvars(template)

        # Now call special functions as appropriate
        template = self._call_special_functions(filetype, template, **kwargs)

        # Now match on any software product tags
        skip_tag_check = kwargs.get('skip_tag_check', None)
        if not skip_tag_check:
            template = re.sub(r'tags/(v?[0-9._]+)', r'\1', template, count=1)

        return self._check_compression(template)

    @staticmethod
    def check_modules(template, permanent=None):
        ''' Check for any existing Module path environment

        For software product paths, overrides the tree environment paths with existing
        original envvars from os.environ that may be set from shell bash or module environments.
        Checks the original os.environ for any environment variables and replaces the template
        envvar with the original os version.  Ignores all SAS data paths.  If permanent is True,
        then permanently replaces the envvar in existing os.environ with the original.
        Assumes original environment variables points to definitions created by module files or bash
        profiles.

        Parameters:
            template (str):
                The path template to check
            permanent (bool):
                If True, sets the original module environment variable into os.environ

        Returns:
            The template with updated environment variable path
        '''
        # if template starts with $SAS_BASE_DIR, then do nothing
        expanded_template = _expandvars(template)
        if expanded_template.startswith(os.getenv("SAS_BASE_DIR")):
            return template

        # match template against envvar $ENVVAR_DIR
        ev_match = re.match(r'^\$(\w+)', template)
        if ev_match:
            envvar = ev_match.group()
            envvar_name = ev_match.groups()[0]
            orig_os = tree.get_orig_os_environ()
            if envvar_name in orig_os:
                orig_envvar = orig_os.get(envvar_name)
                # update the real os environment
                if permanent:
                    os.environ[envvar_name] = orig_envvar
                return template.replace(envvar, orig_envvar)
            else:
                log.info('No existing envvar found for {0}. Returning input template'.format(envvar_name))
                return template

    def _remove_compression(self, template):
        ''' remove a compression suffix '''
        is_comp = re.search(self._comp_regex, template)
        if is_comp:
            temp_split = re.split(self._comp_regex, template)
            template = temp_split[0]
        return template

    def _add_compression_wild(self, template):
        ''' add a compression wildcard '''
        is_comp = re.search(self._comp_regex, template)
        if is_comp:
            for comp in self._compressions:
                template = template.replace(comp, '*')
        else:
            template = template + '*'
        return template

    def _check_compression(self, template):
        ''' check if filepath is actually compressed '''

        exists = self.exists('', full=template)
        if exists:
            return template

        # check if file is not compressed compared to template
        is_comp = re.search(self._comp_regex, template)
        if is_comp:
            base = os.path.splitext(template)[0]
            exists = self.exists('', full=base)
            if exists:
                return base

        # check if file on disk is actually compressed compared to template
        alternates = glob(template + '*')
        if alternates:
            suffixes = list(set([re.search(self._comp_regex, c).group(0)
                                 for c in alternates if re.search(self._comp_regex, c)]))
            if suffixes:
                assert len(suffixes) == 1, 'should only be one suffix per file template '
                if not template.endswith(suffixes[0]):
                    template = template + suffixes[0]

        return template

    def _call_special_functions(self, filetype, template, **kwargs):
        ''' Call the special functions found in a template path

        Calls special functions indicated by %methodname found in the
        sdss_paths.ini template file, and replaces the %location in the path
        with the returned content.

        Parameters:
            filetype (str):
                template name of file
            template (str):
                the template path
            kwargs (dict):
                Any kwargs needed to pass into the methods

        Returns:
            The expanded template path
        '''
        # Now call special functions as appropriate
        functions = re.findall(self._special_fxn_pattern, template)
        if not functions:
            return template

        for function in functions:
            try:
                method = getattr(self, function[1:-1])
            except AttributeError:
                return None
            else:
                value = method(filetype, **kwargs)
                template = template.replace(function, value)

        return template

    def get_netloc(self, netloc=None, sdss=None, sdss5=None, dtn=None, svn=None, mirror=None):
        ''' Get a net url domain

        Returns an SDSS url domain location.  Options are the SDSS SAS domain, the rsync download
        server, the svn server, or the mirror data domain.  The mirror data domain is retrieved
        either by the ``mirror`` input keyword argument or by the ``path.mirror`` attribute.

        Parameters
        ----------
            netloc : str
                An exact net location to return directly
            sdss : bool
                If True, returns SDSS data domain: data.sdss.org
            sdss5 : bool
                If True, sets the SDSS-V data domain: data.sdss5.org
            dtn : bool
                If True, returns SDSS rsync server domain: dtn.sdss.org
            svn: bool
                If True, returns SDSS svn domain: svn.sdss.org
            mirror: bool
                If True, return SDSS mirror domain: data.mirror.sdss.org.

        Returns
        -------
            An http domain name
        '''
        if netloc:
            return netloc

        if dtn:
            return self._netloc["dtn"]
        elif sdss:
            return self._netloc["sdss"]
        elif sdss5:
            return self._netloc["sdss5"]
        elif mirror or self.mirror:
            return self._netloc["mirror"]
        elif svn:
            return '{0}{1}'.format(self._netloc["svn"], "/public" if self.public else '')
        else:
            return self._netloc["sdss5"] if self.release == "sdss5" else self._netloc["sdss"]

    def set_netloc(self, netloc=None, sdss=None, sdss5=None, dtn=None, svn=None, mirror=None):
        ''' Set a url domain location

        Sets an SDSS url domain location.  Options are the SDSS SAS domain, the rsync download
        server, the svn server, or the mirror data domain.  The mirror data domain is set
        either by the ``mirror`` input keyword argument or by the ``path.mirror`` attribute.

        Parameters
        ----------
            netloc : str
                An exact net location to use directly
            sdss : bool
                If True, sets the SDSS-IV data domain: data.sdss.org
            sdss5 : bool
                If True, sets the SDSS-V data domain: data.sdss5.org
            dtn : bool
                If True, sets the SDSS rsync server domain: dtn.sdss.org
            svn: bool
                If True, sets the SDSS svn domain: svn.sdss.org
            mirror: bool
                If True, sets the SDSS mirror domain: data.mirror.sdss.org.

        '''
        self.netloc = self.get_netloc(netloc=netloc, sdss=sdss, sdss5=sdss5, dtn=dtn, svn=svn, mirror=mirror)

    def set_remote_base(self, scheme='https'):
        self.remote_base = self.get_remote_base(scheme=scheme or 'https')

    def get_remote_base(self, scheme="https", svn=None):
        ''' Get the remote base path

        Parameters
        ----------
        scheme : str
            The url scheme. Either "https" or "rsync".
        svn : bool
            If True, uses the svn url domain svn.sdss.org as the netloc
        '''
        netloc = self.netloc
        if svn:
            netloc = self.get_netloc(svn=True)
        if self.public or scheme == "https":
            remote_base = "{scheme}://{netloc}".format(scheme=scheme, netloc=netloc)
        else:
            user = "sdss5" if self.release == "sdss5" else "sdss"
            remote_base = "{scheme}://{user}@{netloc}".format(scheme=scheme, user=user, netloc=netloc)
        return remote_base

    def set_base_dir(self, base_dir=None):
        ''' Sets the base directory

        Sets the ``base_dir`` attribute.  Defaults to $SAS_BASE_DIR.  Can be
        overridden by passing in ``base_dir`` keyword argument.  The ``base_dir`` sets
        the beginning part of all local paths.

        Parameters
        ----------
            base_dir : str
                A directory path to use as the base

        '''
        if base_dir:
            self.base_dir = join(base_dir, '')
        else:
            try:
                self.base_dir = join(os.environ['SAS_BASE_DIR'], '')
            except Exception:
                pass

    @staticmethod
    def yield_product_root():
        ''' yields a product root environment name '''

        for root in tree._product_roots:
            yield root

    def find_location(self, filetype, **kwargs):
        ''' Finds a relative location of a product path

        Attempts to find a relative path location for a software product path.
        Loops over all product_roots defined in the tree and tests if a relative location
        can be extracted, i.e. if the path starts with a given root path.  The root environment
        paths searched are the following in order of precendence:
        PRODUCT_ROOT, SDSS_SVN_ROOT, SDSS_INSTALL_PRODUCT_ROOT, SDSS_PRODUCT_ROOT,
        SDSS4_PRODUCT_ROOT. If no root is found uses one directory up from SAS_BASE_DIR.

        Parameters
        ----------
        filetype : str
            File type parameter.
        kwargs : dict
            Path definition keyword arguments

        Returns
        -------
            The relative path location (to the base_dir)

        '''

        # loop over all potential git/svn product roots
        loc = None
        for root in tree._product_roots:
            loc = self._extract_location(filetype, base_dir=os.getenv(root), **kwargs)
            if loc:
                self.product_root = os.getenv(root)
                break
        return loc

    def _extract_location(self, filetype, base_dir=None, **kwargs):
        ''' Extracts the relative path location of the file

        Parameters
        ----------
        filetype : str
            File type parameter.
        base_dir : str
            A root directory to use as the base.  Defaults to SAS_BASE_DIR.

        Returns
        -------
            The relative path location (to the base_dir)

        '''
        full = kwargs.get('full', None)
        if not full:
            full = self.full(filetype, **kwargs)

        self.set_base_dir(base_dir=base_dir)
        location = full[len(self.base_dir):] if full and full.startswith(self.base_dir) else None
        return location

    def location(self, filetype, base_dir=None, **kwargs):
        """Return the location of the relative sas path of a given type of file.

        Parameters
        ----------
        filetype : str
            File type parameter.
        base_dir : str
            A root directory to use as the base.  Defaults to SAS_BASE_DIR.

        Returns
        -------
            The relative path location (to the base_dir)
        """

        # extract the location using SAS_BASE_DIR as the base
        location = self._extract_location(filetype, base_dir=base_dir, **kwargs)

        # attempt to find a product location
        if not location:
            location = self.find_location(filetype, **kwargs)

        if location and '//' in location:
            location = location.replace('//', '/')

        return location

    def url(self, filetype, base_dir=None, sasdir='sas', **kwargs):
        """Return the url of a given type of file.

        Parameters
        ----------
        filetype : str
            File type parameter.
        base_dir : str
            A root directory to use as the base.  Defaults to SAS_BASE_DIR.

        Returns
        -------
        full : str
            The sas url to the file.
        """

        # determine the remote domain location
        remote_base = self.remote_base
        full = self.full(filetype, skip_tag_check=True, **kwargs)
        # if not on the SAS, assume it is an SVN product path
        if not full.startswith(os.getenv("SAS_BASE_DIR")):
            remote_base = self.get_remote_base(svn=True)
            sasdir = ''

        # get the location and set the url
        location = self.location(filetype, skip_tag_check=True, base_dir=base_dir, **kwargs)
        if not location:
            raise AccessError('Cannot construct url.  A path.location could not extracted. ')

        # create the url path
        url = join(remote_base, sasdir, location) if remote_base and location else None
        if not is_posix:
            url = url.replace(sep, '/')

        # handle edge case when a full path is passed in as path.url('', full=full)
        # sanity check on svn tags
        if 'svn.sdss.org' in url:
            tag_match = re.search(r'tags/(v?[0-9._]+)', url)
            if not tag_match:
                url = re.sub(r'(/v?[0-9._]+/)', r'/tags\1', url, count=1)
        return url


def _expandvars(template):
    ''' Recursively run os.path.expandvars

    Recursively calls os.path.expandvars

    Parameters:
        template (str):
            sdss_access path template

    Return:
        A path template with expanded environment variables
    '''
    template = os.path.expandvars(template)
    if template.startswith('$'):
        # if the envvar isn't in os.environ, then exit
        envvar = template.split('/', 1)[0]
        if envvar[1:] not in os.environ:
            return template

        # recurse down
        return _expandvars(template)
    return template


class Path(BasePath):
    """Class for construction of paths in general.  Sets a particular template file.

    Parameters
    ----------
    release : str
        The release name, e.g. 'DR15', 'MPL-9'.
    public : bool
        If True, uses public urls.  Only needed for public data releases. Automatically set to True when release contains "DR".
    mirror : bool
        If True, uses the mirror data domain url.  Default is False.
    verbose: bool
        If True, turns on verbosity.  Default is False.
    force_modules : bool
        If True, forces svn or github software products to use any existing local Module environment paths, e.g. PLATEDESIGN_DIR
    preserve_envvars : bool | list
        Flag(s) to indicate some or all original environment variables to preserve

    Attributes
    ----------
    templates : dict
        The set of templates read from the configuration file.

    """

    def __init__(self, release=None, public=False, mirror=False, verbose=False, force_modules=None,
                 preserve_envvars=None):
        super(Path, self).__init__(release=release, public=public, mirror=mirror, verbose=verbose,
                                   force_modules=force_modules, preserve_envvars=preserve_envvars)

    def __repr__(self):
        rep = super().__repr__()
        return rep.replace('BasePath', 'Path')

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

    def plategrp(self, filetype, **kwargs):
        ''' Returns plate group subdirectory

        Parameters
        ----------
        filetype : str
            File type parameter.
        plate : int or str
            Plate ID number.  Will be converted to int internally.

        Returns
        -------
        plategrp : str
            Plate group directory in the format ``NNNNXX``.

        '''

        plate = kwargs.get('plate', kwargs.get('plateid', None))
        if not plate:
            return 'XX'
        return '{:0>4d}XX'.format(int(plate) // 100)

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

    def definitiondir(self, filetype, **kwargs):
        """Returns definition subdirectory in :envvar:`PLATELIST_DIR` of the form: ``NNNNXX``.

        Parameters
        ----------
        filetype : str
            File type parameter.
        designid : int or str
            Design ID number.  Will be converted to int internally.

        Returns
        -------
        definitiondir : str
            Definition directory in the format ``NNNNXX``.
        """

        designid = int(kwargs['designid'])
        designid100 = designid // 100
        subdir = "{:0>4d}".format(designid100) + "XX"
        return subdir

    def healpixgrp(self, filetype, **kwargs):
        ''' Returns HEALPIX group subdirectory

        Parameters
        ----------
        filetype : str
            File type parameter.
        healpix : int or str
            HEALPix number.  Will be converted to int internally.

        Returns
        -------
        healpixgrp : str
            HEALPix group directory, HEALPix//1000.

        '''

        healpix = int(kwargs['healpix'])
        subdir = "{:d}".format(healpix // 1000)
        return subdir

    def cat_id_groups(self, filetype, **kwargs):
        ''' 
        Return a folder structure to group data together based on their catalog
        identifier so that we don't have too many files in any one folder.
        
        Parameters
        ----------
        filetype : str
            File type parameter.
        cat_id : int or str
            SDSS-V catalog identifier
        
        Returns
        -------
        catalogid_group : str
            A set of folders.
        '''
        # with k = 100 then even with 10 M sources, each folder will have ~1,000 files
        k = 100
        cat_id = int(kwargs['cat_id'])
        return f"{(cat_id // k) % k:0>2.0f}/{cat_id % k:0>2.0f}"

    def component_default(self, filetype, **kwargs):
        ''' Return the component name, if given.

        The component designates a stellar or planetary body following the 
        Washington Multiplicity Catalog, which was adopted by the XXIV meeting
        of the International Astronomical Union. When no component is given,
        the star is assumed to be without a discernible companion. When a
        component is given it follows the system (Hessman et al., arXiv:1012.0707):

        – the brightest component is called “A”, whether it is initially resolved 
          into sub-components or not;
        – subsequent distinct components not contained within “A” are labeled “B”, 
          “C”, etc.;
        – sub-components are designated by the concatenation of on or more suffixes 
          with the primary label, starting with lowercase letters for the 2nd 
          hierarchical level and then with numbers for the 3rd.
        
        Parameters
        ----------
        filetype : str
            File type parameter. This argument is not used here, but is required for 
            all special functions in the `sdss_access` product.
        component : str [optional]
            The component name as given by the fields.
        
        Returns
        -------
        component : str
            The component name if given, otherwise a blank string.
        '''
        # the (..) or '' resolves None to ''
        return str(kwargs.get('component', '') or '')

    def apgprefix(self, filetype, **kwargs):
        ''' Returns APOGEE prefix using telescope/instrument.

        Parameters
        ----------
        filetype : str
            File type parameter.
        telescope : str
            The APOGEE telescope (apo25m, lco25m, apo1m).
        instrument : str
            The APOGEE instrument (apogee-n, apogee-s).

        Returns
        -------
        prefix : str
            The APOGEE prefix (ap/as).

        '''

        telescope = kwargs.get('telescope', None)
        if telescope is not None:
            prefix = {'apo25m': 'ap', 'apo1m': 'ap', 'lco25m': 'as'}
            if telescope not in prefix:
                raise ValueError(f'{telescope} not in allowed list of prefixes')
            return prefix[telescope]

        instrument = kwargs.get('instrument', None)
        if instrument is not None:
            prefix = {'apogee-n': 'ap', 'apogee-s': 'as'}
            if instrument not in prefix:
                raise ValueError(f'{instrument} not in allowed list of prefixes')
            return prefix[instrument]

        return ''

    def apginst(self, filetype, **kwargs):
        ''' Returns APOGEE "instrument" from "telescope".

        Parameters
        ----------
        filetype : str
            File type parameter.
        telescope : str
            The APOGEE telescope (apo25m, lco25m, apo1m).

        Returns
        -------
        instrument : str
            The APOGEE instrument (apogee-n, apogee-s).

        '''

        telescope = kwargs.get('telescope', None)
        if telescope is not None:
            instrument = {'apo25m': 'apogee-n', 'apo1m': 'apogee-n', 'lco25m': 'apogee-s'}
            if telescope not in instrument:
                raise ValueError(f'{telescope} not in allowed list of prefixes')
            return instrument[telescope]
        return ''

    def configgrp(self, filetype, **kwargs):
        ''' Returns configuration summary file group subdirectory

        Parameters
        ----------
        filetype : str
            File type parameter.
        configid : int or str
            Configuration ID number.  Will be converted to int internally.

        Returns
        -------
        configgrp : str
            Configuration group directory in the format ``NNNNXX``.

        '''

        configid = kwargs.get('configid', None)
        if not configid:
            return '0000XX'
        return '{:0>4d}XX'.format(int(configid) // 100)

    def isplate(self, filetype, **kwargs):
        ''' Returns the plate flag for BOSS idlspec2d run2d versions that utilize it

        Parameters
        ---------
        filetype : str
            File type paramter
        run2d : str
            BOSS idlspec2d run2d version

        Returns
        -------
        isplate : str
            isplate flag = 'p' for relevent run2d plates else flag = ''
        '''

        run2d = kwargs.get('run2d', None)
        if not run2d:
            return ''
        if run2d in ['v6_0_1','v6_0_2', 'v6_0_3', 'v6_0_4']:
            return 'p'
        return ''

    def pad_fieldid(self, filetype, **kwargs):
        ''' Returns the fieldid zero padded to its proper length for the BOSS idlspec2d run2d version

        Parameters
        ---------
        filetype : str
            File type paramter
        run2d : str
            BOSS idlspec2d run2d version
        fieldid : str or int
            Field ID number. Will be converted to str internally.

        Returns
        -------
        fieldid : str
            padd_fieldid in the form of N*'0' where N is the number of necessary zeros to pad fieldid
        '''

        fieldid = kwargs.get('fieldid', None)
        run2d = kwargs.get('run2d', None)

        if (not run2d) & (not fieldid):
            return ''
        if run2d in ['v6_0_1','v6_0_2', 'v6_0_3', 'v6_0_4']:
            return str(fieldid)
        return str(fieldid).zfill(6)


class AccessError(Exception):
    pass
