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
                             [('apStar', '@healpixgrp',
                               {'apred': 'r12', 'apstar': 'stars', 'telescope': 'apo25m',
                                'healpix': '12345', 'obj': '12345'},
                               'r12/stars/apo25m/12/12345/apStar-r12-apo25m-12345.fits')],
                             ids=['apStar'])
    def test_apogee_paths(self, path, name, special, keys, exp):
        assert special in path.templates[name]
        full = path.full(name, **keys)
        assert exp in full

    @pytest.mark.parametrize('name, special, keys, exp',
                             [('confSummary', '@configgrp', {'configid': 1234, 'obs': 'apo'},
                               '0012XX/confSummary-1234.par'),
                              ('apField', '@apgprefix', {'telescope': 'apo25m', 'apred': 'r12', 'field': '2J01'},
                               'redux/r12/stars/apo25m/2J01/apField-2J01.fits'),
                              ('apField', '@apgprefix', {'telescope': 'lco25m', 'apred': 'r12', 'field': '2J01'},
                               'redux/r12/stars/lco25m/2J01/asField-2J01.fits'),
                              ('apHist', '@apgprefix', {'apred': 'r12', 'mjd': '52123', 'chip':'b', 'instrument': 'apogee-n'},
                               'r12/exposures/apogee-n/52123/apHist-b-52123.fits'),
                              ('spField', '@isplate', {'run2d': 'v6_0_4', 'mjd': '59187', 'fieldid': '15007'},
                                'v6_0_4/15007p/spField-15007-59187.fits'),
                              ('spField', '@pad_fieldid', {'run2d': 'v6_0_8', 'mjd': '59630', 'fieldid': '021160'},
                                'v6_0_8/021160/spField-021160-59630.fits'),
                              ('spField', '@pad_fieldid', {'run2d': 'v6_0_8', 'mjd': '59760', 'fieldid': '112359'},
                                'v6_0_8/112359/spField-112359-59760.fits'),
                              ('spFrame', '@pad_fieldid', {'run2d': 'v6_0_8', 'br': 'b', 'id': '1', 'frame': '5432', 'fieldid':'1234'},
                                'v6_0_8/001234/spFrame-b1-00005432.fits.gz'),
                              ('spFrame', '@pad_fieldid', {'run2d': 'v6_0_4', 'br': 'b', 'id': '1', 'frame': '5432', 'fieldid':'1234'},
                                'v6_0_4/1234p/spFrame-b1-00005432.fits.gz'),
                              ('spField', '@pad_fieldid', {'run2d': 'v6_1_1', 'mjd': '59630', 'fieldid': '*'},
                                'v6_1_1/*/spField-*-59630.fits')],
                             ids=['configgrp', 'apgprefix-apo', 'apgprefix-lco', 'apgprefix-ins',
                                  'isplate-v6_0_4','pad_fieldid-5','pad_fieldid-6', 'frame-pad', 'frame-nopadp', 'pad_fieldid-*'])
    def test_special_function(self, path, name, special, keys, exp):
        assert special in path.templates[name]
        full = path.full(name, **keys)
        assert exp in full

    @pytest.mark.parametrize('name, keys', [('specLite', ['fieldid', 'catalogid', 'run2d', 'mjd']),
                                            ('mwmStar', ['component', 'sdss_id', 'v_astra']),])
    def test_lookup_keys(self, path, name, keys):
        realkeys = path.lookup_keys(name)
        assert set(keys) == set(realkeys)

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
