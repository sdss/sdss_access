#!/usr/bin/env python
# encoding: utf-8

from __future__ import absolute_import, division, print_function, unicode_literals

from pkg_resources import parse_version
import os

import yaml

# set up the TREE, but match the TREE_VER if it is already there
from tree import Tree

# Inits the logging system. Only shell logging, and exception and warning catching.
# File logging can be started by calling log.start_file_logger(name).
from .misc import log

# check if posix-based operating system
from os import name
is_posix = ( name == "posix" )

# set up the TREE, but match the TREE_VER if it is already there
from tree import Tree
config = os.environ.get('TREE_VER', 'sdsswork')
tree = Tree(config=config)
log.debug("SDSS_ACCESS> Using %r" % tree)

from .path import Path as SDSSPath, AccessError
from .sync import HttpAccess, Access, BaseAccess, RsyncAccess, CurlAccess


NAME = 'sdss_access'

# Loads config
yaml_version = parse_version(yaml.__version__)
with open(os.path.dirname(__file__) + '/etc/{0}.cfg'.format(NAME)) as ff:
    if yaml_version >= parse_version('5.1'):
        config = yaml.load(ff, Loader=yaml.FullLoader)
    else:
        config = yaml.load(ff)

__version__ = '0.2.10'
