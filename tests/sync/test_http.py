# !/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Filename: test_http.py
# Project: sync
# Author: Brian Cherinka
# Created: Monday, 16th September 2019 2:51:23 pm
# License: BSD 3-clause "New" or "Revised" License
# Copyright (c) 2019 Brian Cherinka
# Last Modified: Monday, 16th September 2019 3:08:02 pm
# Modified By: Brian Cherinka


from __future__ import print_function, division, absolute_import
import os
import pytest
from sdss_access import tree
from sdss_access.sync import HttpAccess


@pytest.fixture()
def monkeyprod(tmpdir, monkeypatch):
    ''' fixture to monkeypatch the sas_base_dir '''
    orig = os.getenv("PRODUCT_ROOT")
    tmppath = tmpdir / 'software'
    os.makedirs(tmppath, exist_ok=True)
    monkeypatch.setenv('PRODUCT_ROOT', str(tmppath))
    tree.set_product_root(root=str(tmppath))
    yield
    os.environ["PRODUCT_ROOT"] = orig
    tree.set_product_root()


class TestHttp(object):

    def test_http(self, http, datapath):
        name = http.release.lower() if http.release and 'dr' in http.release.lower() else datapath['work']
        path = http.url(datapath['name'], **datapath['params'])
        assert datapath['location'] in path
        assert 'https://data.sdss.org' in path
        assert name in path

    def test_svn_exist(self):
        http = HttpAccess(release='DR15')
        http.remote()
        exists = http.exists('mangapreimg', designid=8405, designgrp='D0084XX',
                             mangaid='1-42007', remote=True)
        assert exists is True

    def test_svn_get(self, monkeyprod):
        http = HttpAccess(release='DR15')
        http.remote()
        full = http.full('mangapreimg', designid=8405, designgrp='D0084XX',
                         mangaid='1-42007', remote=True)

        http.get('mangapreimg', designid=8405, designgrp='D0084XX',
                 mangaid='1-42007', remote=True)

        assert os.path.exists(full)
