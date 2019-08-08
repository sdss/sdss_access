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
import os
import re
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

    def test_lookup_names(self, path):
        assert 'mangacube' in path.lookup_names()

    @pytest.mark.parametrize('name, keys', [('mangacube', ['drpver', 'ifu', 'plate']),
                                            ('plateLines', ['plateid'])])
    def test_lookup_keys(self, path, name, keys):
        realkeys = path.lookup_keys(name)
        assert set(keys) == set(realkeys)

    @pytest.mark.parametrize('name, special, keys, exp',
                             [('plateLines', '%platedir', {'plateid': 8485},
                               '0084XX/008485/plateLines-008485.png'),
                              ('plateLines', '%platedir', {'plateid': 11002},
                               '0110XX/011002/plateLines-11002.png'),
                              ('spAll', '%spectrodir', {'run2d': 103},
                               'sas/sdsswork/sdss/spectro'),
                              ('spAll', '%spectrodir', {'run2d': 100},
                               'sas/ebosswork/eboss/spectro')],
                             ids=['platedir_p4', 'platedir_p5', 'spectrodir_r1', 'spectrodir_r2'])
    def test_special_function(self, path, name, special, keys, exp):
        assert special in path.templates[name]
        full = path.full(name, **keys)
        assert exp in full

    def test_envvar_expansion(self, path):
        name = 'mangacube'
        assert '$MANGA_SPECTRO_REDUX' in path.templates[name]
        full = path.full(name, drpver='v2_4_3', plate=8485, ifu=1901)
        exp = 'sas/mangawork/manga/spectro/redux/v2_4_3/8485'
        assert exp in full

    @pytest.mark.parametrize('name, example, keys',
                             [('mangacube',
                               'mangawork/manga/spectro/redux/v2_4_3/8485/stack/manga-8485-1901-LOGCUBE.fits.gz',
                               {'drpver': 'v2_4_3', 'plate': '8485', 'ifu': '1901'}),
                              ('REJECT_MASK', 'ebosswork/eboss/lss/reject_mask/mask.html',
                               {'type': 'mask', 'format': 'html'}),
                              ('fpC', 'ebosswork/eboss/photo/redux/1/45/objcs/3/fpC-000045-g3-0123.fit',
                               {'rerun': '1', 'field': '0123', 'filter': 'g', 'camcol': '3', 'run': '000045'}),
                              ('galaxy', 'ebosswork/eboss/lss/galaxy_DR12v1.0_1_n.fits.gz', 
                               {'sample': '1', 'dr': 'DR12', 'version': 'v1.0', 'ns': 'n'})],
                             ids=['mangacube', 'reject', 'fpc', 'galaxy'])
    def test_extract(self, path, name, example, keys):
        fullpath = os.path.join(os.environ['SAS_BASE_DIR'], example)
        realkeys = path.extract(name, fullpath)
        assert keys == realkeys

    def test_extract_source(self, path):
        code = path._find_source(path.full)
        assert 'def full(self' in code
        assert 'template = self._call_special_functions' in code

    def full(self, path):
        full = path.full('mangacube', drpver='v2_4_3', plate=8485, ifu='*')
        return full

    def test_location(self, path):
        full = self.full(path)
        loc = path.location('', full=full)
        assert 'mangawork/manga/spectro/redux/v2_4_3/8485/stack/manga-8485-*-LOGCUBE.fits.gz' in loc

    def test_name(self, path):
        full = self.full(path)
        name = path.name('', full=full)
        assert 'manga-8485-*-LOGCUBE.fits.gz' in name

    def test_dir(self, path):
        full = self.full(path)
        d = path.dir('', full=full)
        assert d.endswith('mangawork/manga/spectro/redux/v2_4_3/8485/stack')

    def test_url(self, path):
        full = self.full(path)
        url = path.url('', full=full)
        assert 'https://data.sdss.org/sas/mangawork/manga/spectro/redux/' in url

    @pytest.mark.parametrize('method', [('one'), ('random')])
    def test_onerandom(self, path, method):
        full = self.full(path)
        meth = path.__getattribute__(method)
        one = meth('', full=full)
        if one:
            data = one if method == 'one' else one[0]
            assert re.search(r'(.*?)manga-8485-(\d+)-LOGCUBE(.*?)', data)

    def test_expand(self, path):
        full = self.full(path)
        ex = path.expand('', full=full)
        if ex:
            assert len(ex) > 1

    def test_any(self, path):
        full = self.full(path)
        a = path.any('', full=full)
        if a:
            assert a is True

    def test_refine(self, path):
        full = self.full(path)
        n = path.expand('', full=full)
        if not n:
            return
        items = path.refine(n, r'(.*?)-19\d{2}-(.*?)')
        for item in items:
            assert re.search('8485-190[1-2]', item)
