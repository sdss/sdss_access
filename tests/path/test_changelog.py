# !usr/bin/env python
# -*- coding: utf-8 -*-
#

from sdss_access.path.changelog import compute_changelog, get_available_releases, get_path_templates


def test_changelog():
    cc = compute_changelog('dr17', 'dr16')

    assert cc['releases'] == {'new': 'dr17', 'old': 'dr16'}
    assert cc['paths']['new']['apogee_astronn'] == '$APOGEE_ASTRONN/apogee_astroNN-{release}.fits'


def test_get_templates():
    temps = get_path_templates('mangaimage')
    assert temps['sdsswork'] is None
    assert temps['DR17'] == '$MANGA_SPECTRO_REDUX/{drpver}/{plate}/images/{ifu}.png'
    assert temps['DR14'] ==  '$MANGA_SPECTRO_REDUX/{drpver}/{plate}/{dir3d}/images/{ifu}.png'


def temp_get_releases():
    rels = get_available_releases()
    assert 'IPL2' in rels
    assert 'DR14' in rels

    rels = get_available_releases(public=True)
    assert 'IPL2' not in rels
