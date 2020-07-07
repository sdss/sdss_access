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
from sdss_access import tree
from sdss_access.path import Path
from tests.conftest import gzcompress, gzuncompress


class TestPath(object):

    def test_missing_keys(self, path):
        with pytest.raises(KeyError) as cm:
            full = path.full('mangacube')
        assert 'Missing required keyword arguments:' in str(cm.value)

    def test_public(self):
        path = Path()
        url = path.url('mangacube', drpver='v2_3_1', plate=8485, ifu='1901', wave='LOG')
        assert 'mangawork' in url

        release = 'dr14'
        path = Path(public=True, release=release)
        url = path.url('mangacube', drpver='v2_3_1', plate=8485, ifu='1901', wave='LOG')
        assert release in url

    @pytest.mark.parametrize('place, exp', [('local', False), ('remote', True)])
    def test_existence(self, path, place, exp):
        full = path.full('mangaimage', drpver='v2_5_3', plate=8116, ifu=1901, dir3d='mastar')
        exists = path.exists('', full=full, remote=(place == 'remote'))
        assert exp == exists

    def test_lookup_names(self, path):
        assert 'mangacube' in path.lookup_names()

    @pytest.mark.parametrize('name, keys', [('mangacube', ['drpver', 'ifu', 'plate', 'wave']),
                                            ('plateLines', ['plateid'])])
    def test_lookup_keys(self, path, name, keys):
        realkeys = path.lookup_keys(name)
        assert set(keys) == set(realkeys)

    @pytest.mark.parametrize('name, special, keys, exp',
                             [('plateLines', '@platedir', {'plateid': 8485},
                               '0084XX/008485/plateLines-008485.png'),
                              ('plateLines', '@platedir', {'plateid': 11002},
                               '0110XX/011002/plateLines-11002.png'),
                              ('spAll', '@spectrodir', {'run2d': 103},
                               'sas/sdsswork/sdss/spectro'),
                              ('spAll', '@spectrodir', {'run2d': 100},
                               'sas/ebosswork/eboss/spectro')],
                             ids=['platedir_p4', 'platedir_p5', 'spectrodir_r1', 'spectrodir_r2'])
    def test_special_function(self, path, name, special, keys, exp):
        assert special in path.templates[name]
        full = path.full(name, **keys)
        assert exp in full

    def test_envvar_expansion(self, path):
        name = 'mangacube'
        assert '$MANGA_SPECTRO_REDUX' in path.templates[name]
        full = path.full(name, drpver='v2_4_3', plate=8485, ifu=1901, wave='LOG')
        exp = 'sas/mangawork/manga/spectro/redux/v2_4_3/8485'
        assert exp in full

    @pytest.mark.parametrize('name, example, keys',
                             [('mangacube',
                               'mangawork/manga/spectro/redux/v2_4_3/8485/stack/manga-8485-1901-LOGCUBE.fits.gz',
                               {'drpver': 'v2_4_3', 'plate': '8485', 'ifu': '1901', 'wave': 'LOG'}),
                              ('REJECT_MASK', 'ebosswork/eboss/lss/reject_mask/mask.html',
                               {'type': 'mask', 'format': 'html'}),
                              ('fpBIN', 'ebosswork/eboss/photo/redux/1/45/objcs/3/fpBIN-000045-g3-0123.fit',
                               {'rerun': '1', 'field': '0123', 'filter': 'g', 'camcol': '3', 'run': '000045'}),
                              ('galaxy', 'ebosswork/eboss/lss/galaxy_DR12v1.0_1_n.fits.gz',
                               {'sample': '1', 'dr': 'DR12', 'version': 'v1.0', 'ns': 'n'})],
                             ids=['mangacube', 'reject', 'fpbin', 'galaxy'])
    def test_extract(self, path, name, example, keys):
        fullpath = os.path.join(os.environ['SAS_BASE_DIR'], example)
        realkeys = path.extract(name, fullpath)
        assert keys == realkeys

    def test_extract_source(self, path):
        code = path._find_source(path.full)
        assert 'def full(self' in code
        assert 'template = self._call_special_functions' in code

    def full(self, path, name='mangacube'):
        full = path.full(name, drpver='v2_4_3', plate=8485, ifu='*', wave='LOG')
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

    @pytest.mark.parametrize('copydata',
                             [('mangawork/manga/spectro/redux/v2_4_3/8485/stack/manga-8485-1901-LOGCUBE.fits.gz')],
                             indirect=True, ids=['data'])
    def test_uncompress(self, copydata, monkeysas, path):
        ''' test to find unzipped files with zipped path templates '''
        assert path.templates['mangacube'].endswith('.gz')
        assert path.templates['mangacube'].count('.gz') == 1
        with gzuncompress(copydata) as f:
            full = path.full('mangacube', drpver='v2_4_3', plate=8485, ifu=1901, wave='LOG')
            assert not full.endswith('.gz')
            assert full.count('.gz') == 0
            assert full.endswith('.fits')

    @pytest.mark.parametrize('copydata',
                             [('mangawork/manga/spectro/redux/v2_5_3/8485/images/1901.png')],
                             indirect=True, ids=['data'])
    def test_compress(self, copydata, monkeysas, path):
        ''' test to find zipped files with non-zipped path templates '''
        assert not path.templates['mangaimage'].endswith('.gz')
        assert path.templates['mangaimage'].count('.gz') == 0
        with gzcompress(copydata) as f:
            full = path.full('mangaimage', drpver='v2_5_3', plate=8485, ifu=1901)
            assert not full.endswith('.png')
            assert full.endswith('.gz')
            assert full.count('.gz') == 1

    def test_uncompress_nofileexists(self, monkeysas, path):
        ''' test if no file exists, full returns original template path '''
        assert path.templates['mangacube'].endswith('.gz')
        full = path.full('mangacube', drpver='v2_4_3', plate=8888, ifu=12345, wave='LOG')
        assert full.endswith('.gz')
        assert full.count('.gz') == 1

    @pytest.mark.parametrize('copymulti',
                             [('mangawork/manga/spectro/redux/v2_4_3/8485/stack/manga-8485-*-LOGCUBE.fits.gz')],
                             indirect=True, ids=['data'])
    @pytest.mark.parametrize('plate, ifu', [(8888, '*'), (8888, 12345),
                                            (8485, 1901), (8485, '*')],
                             ids=['nodata-wild', 'nodata', 'glob', 'glob-wild'])
    def test_compression_wildcards(self, copymulti, monkeysas, path, plate, ifu):
        assert path.templates['mangacube'].endswith('.gz')
        full = path.full('mangacube', drpver='v2_4_3', plate=plate, ifu=ifu, wave='LOG')
        assert full.endswith('.gz')
        assert full.count('.gz') == 1

    @pytest.mark.parametrize('mirror', [(True), (False)])
    def test_netloc(self, mirror):
        ''' test the net location and remote_base '''
        path = Path(mirror=mirror)
        if mirror:
            assert path.netloc == 'data.mirror.sdss.org'
            assert path.remote_base == 'https://data.mirror.sdss.org'
        else:
            assert path.netloc == 'data.sdss.org'
            assert path.remote_base == 'https://data.sdss.org'

    def test_path_versions(self, path):
        ff = path.full('mangaimage', plate=8485, ifu=1901, drpver='v2_4_3')
        assert 'stack' not in ff
        assert path.templates['mangaimage'] == '$MANGA_SPECTRO_REDUX/{drpver}/{plate}/images/{ifu}.png'

        path = Path(release='DR13')
        ff = path.full('mangaimage', plate=8485, ifu=1901, drpver='v2_4_3', dir3d='stack')
        assert 'stack' in ff
        assert path.templates['mangaimage'] == '$MANGA_SPECTRO_REDUX/{drpver}/{plate}/{dir3d}/images/{ifu}.png'

    def test_svn_paths(self, path):
        ff = path.full('mangapreimg', designid=8405, designgrp='D0084XX', mangaid='1-42007')
        assert 'mangapreim/trunk/data' in ff
        assert not ff.startswith(os.getenv("SAS_BASE_DIR"))
        assert ff.startswith(os.getenv("PRODUCT_ROOT"))
        loc = path.location('', full=ff)
        assert loc.startswith('data')

    @pytest.mark.parametrize('dr', [(True), (False)])
    def test_svn_urls(self, dr):
        if dr:
            path = Path(release='DR15')
        else:
            path = Path()
        ff = path.full('mangapreimg', designid=8405, designgrp='D0084XX', mangaid='1-42007')
        url = path.url('', full=ff)
        assert url.startswith('https://svn.sdss.org/')
        if dr:
            assert 'svn.sdss.org/public' in url

    def test_svn_tags(self, path):
        ff = path.full('mangapreimg', designid=8405, designgrp='D0084XX', mangaid='1-42007')
        assert 'mangapreim/trunk/data' in ff

        path = Path(release='DR15')
        ff = path.full('mangapreimg', designid=8405, designgrp='D0084XX', mangaid='1-42007')
        assert 'mangapreim/v2_5/data' in ff

        url = path.url('mangapreimg', designid=8405, designgrp='D0084XX', mangaid='1-42007')
        assert 'mangapreim/tags/v2_5/data' in url

    def test_svn_url_tag(self):
        path = Path(release='DR15')
        ff = path.full('mangapreimg', designid=8405, designgrp='D0084XX', mangaid='1-42007')
        assert 'mangapreim/v2_5/data' in ff

        url1 = path.url('mangapreimg', designid=8405, designgrp='D0084XX', mangaid='1-42007')
        url2 = path.url('', full=ff)

        assert 'mangapreim/tags/v2_5/data' in url1
        assert 'mangapreim/tags/v2_5/data' in url2
        assert url1 == url2

    def test_svn_force_module(self, monkeyoos, path):

        path = Path(release='DR15')
        ff = path.full('mangapreimg', designid=8405, designgrp='D0084XX', mangaid='1-42007')
        assert 'mangapreim/v2_5/data' in ff

        ff = path.full('mangapreimg', designid=8405, designgrp='D0084XX', mangaid='1-42007', force_module=True)
        assert 'mangapreim/trunk/data' in ff

    @pytest.mark.parametrize('tree_ver', [('sdsswork'), ('dr15'), ('sdss5'), ('mpl8')])
    def test_release_from_module(self, monkeypatch, tree_ver):
        monkeypatch.setenv('TREE_VER', tree_ver)
        path = Path()
        assert path.release == tree_ver

    def test_sdss5_paths(self, monkeypatch):
        path = Path(release='sdss5')
        assert 'rsFields' in path.templates
        f1 = path.full('rsFields', plan='001', observatory='APO')

        monkeypatch.setenv('TREE_VER', 'sdss5')
        path = Path()
        assert 'rsFields' in path.templates
        f2 = path.full('rsFields', plan='001', observatory='APO')

        assert f1 == f2


@pytest.fixture()
def monkeyoos(monkeypatch):
    ''' monkeypatch the original os environ from tree '''
    oos = tree.get_orig_os_environ()
    monkeypatch.setitem(oos, "MANGAPREIM_DIR", '/tmpdir/data/manga/mangapreim/trunk')
    yield oos
    monkeypatch.delitem(oos, "MANGAPREIM_DIR", raising=False)
