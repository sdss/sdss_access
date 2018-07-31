# !usr/bin/env python
# -*- coding: utf-8 -*-
#
# Licensed under a 3-clause BSD license.
#
# @Author: Brian Cherinka
# @Date:   2018-07-08 16:31:45
# @Last modified by:   Brian Cherinka
# @Last Modified time: 2018-07-31 15:39:47

from __future__ import print_function, division, absolute_import
import pytest
from sdss_access.path import Path


class TestPath(object):

    def test_missing_keys(self, path):
        with pytest.raises(KeyError) as cm:
            full = path.full('mangacube')
        assert 'Missing required keyword arguments:' in str(cm.value)

    def test_public(self):
        path = Path()
        url = path.url('mangacube', drpver='v2_3_1', plate=8485, ifu='1901')
        assert 'mangawork' in url

        release = 'dr14'
        path = Path(public=True, release=release)
        url = path.url('mangacube', drpver='v2_3_1', plate=8485, ifu='1901')
        assert release in url

    @pytest.mark.parametrize('place, exp', [('local', False), ('remote', True)])
    def test_existence(self, path, place, exp):
        full = path.full('mangaimage', drpver='v2_4_3', plate=8116, ifu=1901, dir3d='mastar')
        exists = path.exists('', full=full, remote=(place == 'remote'))
        assert exp == exists

