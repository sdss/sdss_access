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

@pytest.mark.parametrize('cfg, exp',
                    [('sdss5', 'data.sdss5.org'),
                     ('ipl1', 'data.sdss5.org'),
                     ('dr17', 'data.sdss.org'),
                     ('sdsswork', 'data.sdss.org'),
                     ('mpl9', 'data.sdss.org')],
                    ids=['sdss5', 'ipl1', 'dr17', 'sdsswork', 'mpl9'])
def test_netloc(cfg, exp):
    a = RsyncAccess(release=cfg)
    assert a.netloc == exp
    assert a.remote_base == f'https://{exp}'

@pytest.mark.parametrize('cfg, exp',
                    [('sdss5', 'sdss5'),
                     ('ipl1', 'sdss5'),
                     ('dr17', ''),
                     ('sdsswork', 'sdss'),
                     ('mpl9', 'sdss')],
                    ids=['sdss5', 'ipl1', 'dr17', 'sdsswork', 'mpl9'])
def test_remote_base(cfg, exp):
    a = RsyncAccess(release=cfg)
    a.remote()
    assert a.netloc == 'dtn.sdss.org'
    exp = exp if cfg == 'dr17' else f'{exp}@'
    assert a.remote_base == f'rsync://{exp}dtn.sdss.org'