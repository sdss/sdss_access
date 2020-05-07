#!/usr/bin/env python
# encoding: utf-8

from __future__ import absolute_import, division, print_function, unicode_literals
import os
from sdsstools import get_config, get_logger, get_package_version
from tree import Tree


# check if posix-based operating system
is_posix = (os.name == "posix")


NAME = 'sdss_access'

# init the logger
log = get_logger(NAME)

# set up the TREE, but match the TREE_VER if it is already there
config = os.environ.get('TREE_VER', 'sdsswork')
tree = Tree(config=config)
log.debug("SDSS_ACCESS> Using {0}".format(tree))


# Loads config
config = get_config(NAME)


#__version__ = '1.0.0dev'
__version__ = get_package_version(path=__file__, package_name=NAME)


from .path import Path as SDSSPath, AccessError
from .sync import HttpAccess, Access, BaseAccess, RsyncAccess, CurlAccess
