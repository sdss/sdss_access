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
import pytest
from sdss_access.path import Path


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
