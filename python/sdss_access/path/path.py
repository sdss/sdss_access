from __future__ import division, print_function

import os
import re

try:
    from ConfigParser import RawConfigParser
except ImportError:
    from configparser import RawConfigParser

"""
Module for constructing paths to SDSS files.

Example use case:

    import sdss_access.path
    sdss_path = sdss_access.path.path()
    filename = sdss_path.full('photoObj', run=94, rerun='301', camcol=1, field=100)

Depends on the tree product. In particular requires path templates in:
  $TREE_DIR/data/sdss_paths.ini
"""


class base_path(object):
    """Class for construction of paths in general.

    Attributes
    ----------
    templates : dict
        The set of templates read from the configuration file.
    """
    def __init__(self, pathfile):
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
        return os.path.dirname(self.full(filetype, **kwargs))

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
        return os.path.basename(self.full(filetype, **kwargs))

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


class path(base_path):
    """Derived class.  Sets a particular template file.
    """
    def __init__(self):
        try:
            tree_dir = os.environ['TREE_DIR']
        except KeyError:
            raise NameError("Could not find TREE_DIR in the environment!  Did you set up the tree product?")
        pathfile = os.path.join(tree_dir, 'data', 'sdss_paths.ini')
        super(path, self).__init__(pathfile)

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
