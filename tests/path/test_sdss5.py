# !/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Filename: test_sdss5.py
# Project: path
# Author: Brian Cherinka
# Created: Monday, 12th October 2020 5:37:05 pm
# License: BSD 3-clause "New" or "Revised" License
# Copyright (c) 2020 Brian Cherinka
# Last Modified: Monday, 12th October 2020 5:37:05 pm
# Modified By: Brian Cherinka


from __future__ import print_function, division, absolute_import
import os
import pytest
from sdss_access.path import Path
from sdss_access import config


@pytest.fixture(scope='module')
def path():
    pp = Path(release='sdss5')
    yield pp
    pp = None


class TestSVPaths(object):

    @pytest.mark.parametrize('name, special, keys, exp',
                             [('apStar', '@apgprefix',
                               {'apred': 'r12', 'apstar': 'stars', 'telescope': 'apo25m',
                                'healpix': '12345', 'obj': '12345'},
                               'r12/stars/apo25m/12/12345/apStar-r12-12345.fits')],
                             ids=['apStar'])
    def test_apogee_paths(self, path, name, special, keys, exp):
        assert special in path.templates[name]
        full = path.full(name, **keys)
        assert exp in full
        
    def test_netloc(self, path):
        assert path.netloc == 'data.sdss5.org'

    def assert_orig_sdss5_envvars(self):
        assert os.getenv("ROBOSTRATEGY_DATA") == '/tmp/robodata'
        assert os.getenv("ALLWISE_DIR") == '/tmp/allwise'
        assert os.getenv("EROSITA_DIR") == '/tmp/erosita'

    def assert_updated_sdss5_envvars(self):
        assert 'sdsswork/sandbox/robostrategy' in os.getenv("ROBOSTRATEGY_DATA")
        assert 'sdsswork/target/catalogs/allwise' in os.getenv("ALLWISE_DIR")
        assert 'sdsswork/target/catalogs/eRosita' in os.getenv("EROSITA_DIR")

    def assert_all_envvars(self):
        self.assert_orig_sdss5_envvars()
        assert 'sdsswork/sandbox/robostrategy' not in os.getenv("ROBOSTRATEGY_DATA")

    def assert_subset_envvars(self):
        assert 'sdsswork/sandbox/robostrategy' in os.getenv("ROBOSTRATEGY_DATA")
        assert os.getenv("ROBOSTRATEGY_DATA") != '/tmp/robodata'
        assert os.getenv("ALLWISE_DIR") == '/tmp/allwise'
        assert os.getenv("EROSITA_DIR") == '/tmp/erosita'

    def test_replant_updated(self, monkeysdss5):
        self.assert_orig_sdss5_envvars()
        pp = Path(release='sdss5')
        self.assert_updated_sdss5_envvars()
        assert 'sdsswork/sandbox/robostrategy' in pp.full('rsFields', plan='A', observatory='apo')

    def test_replant_preserve_all_envvars(self, monkeysdss5):
        self.assert_orig_sdss5_envvars()
        pp = Path(release='sdss5', preserve_envvars=True)
        self.assert_all_envvars()
        assert 'tmp/robodata' in pp.full('rsFields', plan='A', observatory='apo')
        assert 'tmp/allwise' in pp.full('allwisecat', ver='1.0', num=1234)

    def test_replant_preserve_subset_envvars(self, monkeysdss5):
        self.assert_orig_sdss5_envvars()
        pp = Path(release='sdss5', preserve_envvars=['ALLWISE_DIR', 'EROSITA_DIR'])
        self.assert_subset_envvars()
        assert 'sdsswork/sandbox/robostrategy' in pp.full('rsFields', plan='A', observatory='apo')
        assert 'tmp/allwise' in pp.full('allwisecat', ver='1.0', num=1234)

    def test_replant_preserve_all_from_config(self, monkeysdss5, monkeypatch):
        monkeypatch.setitem(config, 'preserve_envvars', True)
        self.assert_orig_sdss5_envvars()
        pp = Path(release='sdss5')
        self.assert_all_envvars()
        assert 'tmp/robodata' in pp.full('rsFields', plan='A', observatory='apo')
        assert 'tmp/allwise' in pp.full('allwisecat', ver='1.0', num=1234)

    def test_replant_preserve_subset_from_config(self, monkeysdss5, monkeypatch):
        monkeypatch.setitem(config, 'preserve_envvars', ['ALLWISE_DIR', 'EROSITA_DIR'])
        self.assert_orig_sdss5_envvars()
        pp = Path(release='sdss5')
        self.assert_subset_envvars()
        assert 'sdsswork/sandbox/robostrategy' in pp.full(
            'rsFields', plan='A', observatory='apo')
        assert 'tmp/allwise' in pp.full('allwisecat', ver='1.0', num=1234)
