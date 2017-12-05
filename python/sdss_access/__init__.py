#!/usr/bin/env python
# encoding: utf-8

from __future__ import unicode_literals
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os
import yaml

# Inits the logging system. Only shell logging, and exception and warning catching.
# File logging can be started by calling log.start_file_logger(name).
from .misc import log

from .path import Path as SDSSPath, AccessError
from .sync import HttpAccess, RsyncAccess

NAME = 'sdss_access'

# Loads config
config = yaml.load(open(os.path.dirname(__file__) + '/etc/{0}.cfg'.format(NAME)))


__version__ = '0.2.5dev'


# set up the TREE if it is not already
if 'TREE_DIR' not in os.environ:
    from tree import Tree
    the_tree = Tree()


