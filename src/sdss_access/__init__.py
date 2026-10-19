#!/usr/bin/env python
# encoding: utf-8

from __future__ import annotations

import os

from sdsstools import get_config, get_logger, get_package_version
from tree import Tree


# check if posix-based operating system
is_posix = os.name == "posix"


NAME = "sdss_access"

# init the logger
log = get_logger(NAME)

# set up the TREE, but match the TREE_VER if it is already there
config = os.environ.get("TREE_VER", "sdsswork")
tree = Tree(config=config)
log.debug("SDSS_ACCESS> Using %s", tree)


# Loads config
config = get_config(NAME)


__version__ = get_package_version(path=__file__, package_name=NAME)


from .path import AccessError, Path
from .sync import Access, BaseAccess, CurlAccess, HttpAccess, RsyncAccess
