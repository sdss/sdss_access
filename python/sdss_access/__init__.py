#!/usr/bin/env python
# encoding: utf-8

from __future__ import absolute_import, division, print_function, unicode_literals

import os

import yaml

# set up the TREE, but match the TREE_VER if it is already there
from tree import Tree

# Inits the logging system. Only shell logging, and exception and warning catching.
# File logging can be started by calling log.start_file_logger(name).
from .misc import log

# set up the TREE, but match the TREE_VER if it is already there
from tree import Tree
config = os.environ.get('TREE_VER', 'sdsswork')
tree = Tree(config=config)
log.debug("SDSS_ACCESS> Using %r" % tree)

from .path import Path as SDSSPath, AccessError
from .sync import HttpAccess, RsyncAccess


NAME = 'sdss_access'

# Loads config
with open(os.path.dirname(__file__) + '/etc/{0}.cfg'.format(NAME)) as ff:
    config = yaml.load(ff)


__version__ = '0.2.8dev'


