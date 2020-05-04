# !/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Filename: test_access.py
# Project: sync
# Author: Brian Cherinka
# Created: Thursday, 8th August 2019 6:08:07 pm
# License: BSD 3-clause "New" or "Revised" License
# Copyright (c) 2019 Brian Cherinka
# Last Modified: Tuesday, 12th November 2019 2:56:34 pm
# Modified By: Brian Cherinka


from __future__ import print_function, division, absolute_import
import pytest
from sdss_access.sync import CurlAccess, RsyncAccess
import sdss_access
import sys
if sys.version_info.major == 2:
    import imp as importlib
else:
    import importlib


is_posix = [True, False]
exp = {True: (RsyncAccess, 'rsync'), False: (CurlAccess, 'curl')}


@pytest.fixture(params=is_posix, ids=["is_posix", "is_not_posix"])
def monkey_posix(monkeypatch, request):
    monkeypatch.setattr(sdss_access, 'is_posix', request.param)


def test_access(monkey_posix):
    Access = importlib.reload(sdss_access.sync.access).Access
    core, mode = exp[sdss_access.is_posix]
    assert Access.access_mode == mode
    assert issubclass(Access, core)

