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
from sdss_access import tree, AccessError
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

    def test_http_public_dl(self, monkeyprod):
        http = HttpAccess(release='DR14')
        http.remote()
        full = http.full('spec-lite', run2d='v5_10_0', plateid=3606, mjd=55182, fiberid=537)
        http.get('spec-lite', run2d='v5_10_0', plateid=3606, mjd=55182, fiberid=537)
        assert os.path.exists(full)

    def test_nonetrc_fails(self, monkeyhome):
        ''' test raise error when no netrc present '''
        with pytest.raises(AccessError) as cm:
            http = HttpAccess()
            http.remote()
        assert 'No netrc file found. Please create one.' in str(cm.value)

    def test_nonetrc_public_pass(self, monkeyhome):
        ''' test public access does not fail when no netrc '''
        http = HttpAccess(release='DR14')
        http.remote()
        assert http.public is True
        assert http.auth.username is None
        assert http.auth.ready() is None

    @pytest.mark.parametrize('tree_ver, exp', [('sdsswork', 'work'), ('dr15', 'dr15'),
                                               ('dr13', 'dr13'), ('mpl8', 'work')])
    def test_release_from_module(self, monkeypatch, tree_ver, exp, datapath):
        monkeypatch.setenv('TREE_VER', tree_ver)
        http = HttpAccess()
        full = http.full(datapath['name'], **datapath['params'])
        assert http.release == tree_ver
        assert exp in full

