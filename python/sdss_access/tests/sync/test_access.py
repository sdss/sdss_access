# !/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Filename: test_access.py
# Project: sync
# Author: Brian Cherinka
# Created: Thursday, 8th August 2019 6:08:07 pm
# License: BSD 3-clause "New" or "Revised" License
# Copyright (c) 2019 Brian Cherinka
# Last Modified: Thursday, 8th August 2019 6:18:22 pm
# Modified By: Brian Cherinka


from __future__ import print_function, division, absolute_import
import pytest
from sdss_access.sync import CurlAccess, RsyncAccess, Access
from sdss_access import is_posix

core = RsyncAccess if is_posix else CurlAccess
mode = 'rsync' if is_posix else 'curl'


def test_access():
    assert Access.access_mode == mode
    assert issubclass(Access, core)
    