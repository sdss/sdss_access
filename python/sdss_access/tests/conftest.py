# !usr/bin/env python2
# -*- coding: utf-8 -*-
#
# Licensed under a 3-clause BSD license.
#
# @Author: Brian Cherinka
# @Date:   2017-03-24 12:22:30
# @Last modified by:   Brian Cherinka
# @Last Modified time: 2018-07-08 16:34:37

from __future__ import print_function, division, absolute_import
import os
import pytest

from sdss_access import RsyncAccess
from sdss_access.path import Path


releases = ['MPL-5']
plateifus = ['8485-1901']
mpldict = {'MPL-6': ('v2_3_1', '2.1.3'), 'MPL-5': ('v2_0_1', '2.0.2')}
surveys = ['manga']


@pytest.fixture(scope='session', params=releases)
def get_release(request):
    ''' MaNGA release fixture '''
    return request.param


@pytest.fixture(scope='session', params=plateifus)
def get_plateifu(request):
    ''' MaNGA plateifu fixture '''
    return request.param


class Survey(object):
    ''' Survey class '''
    def __init__(self, survey):
        self.survey = survey
        if self.survey == 'manga':
            self.setup_manga()

    def setup_manga(self):
        self.rsync_kwargs = self.get_rsync_kwargs()

    def get_rsync_kwargs(self):
        if self.survey == 'manga':
            rkwargs = {'plate': None, 'ifu': None, 'drpver': None, 'dapver': None, 'dir3d': None,
                       'mpl': None, 'bintype': '*', 'n': '**', 'mode': '*', 'daptype': '*'}
        return rkwargs

    def set_data(self, release):
        if self.survey == 'manga':
            self.release = release
            self.names = ['mangacube']
            if '4' in release:
                self.names.extend(['mangadefault', 'mangamap'])
            else:
                self.names.extend(['mangadap5'])


@pytest.fixture(scope='session', params=surveys)
def survey(request):
    ''' fixture to generate a survey'''
    survey = Survey(request.param)
    yield survey
    survey = None


@pytest.fixture(scope='session')
def init_manga_survey(survey, get_release, get_plateifu):
    ''' create different surveys with different parameters '''

    drpver, dapver = mpldict[get_release]
    plate, ifu = get_plateifu.split('-')
    survey.rsync_kwargs['drpver'] = drpver
    survey.rsync_kwargs['dapver'] = dapver
    survey.rsync_kwargs['plate'] = plate
    survey.rsync_kwargs['ifu'] = ifu
    survey.set_data(get_release)
    yield survey


@pytest.fixture(scope='module', params=['mangadap5', 'mangacube'])
def data(request, init_manga_survey):
    ''' fixture to generate data '''
    fillkwargs = {'plate': init_manga_survey.rsync_kwargs['plate'], 'ifu': init_manga_survey.rsync_kwargs['ifu'],
                  'drpver': init_manga_survey.rsync_kwargs['drpver'], 'dapver': init_manga_survey.rsync_kwargs['dapver']}
    data_dict = {'mangadefault': {'files': 'mangadap-{plate}-{ifu}-default.fits.gz'.format(**fillkwargs),
                                  'loc': 'mangawork/manga/spectro/analysis/{drpver}/{dapver}/default/{plate}/'.format(**fillkwargs),
                                  'single': 'mangadap-{plate}-{ifu}-default.fits.gz'.format(**fillkwargs),
                                  'count': 1},
                 'mangamap': {'files': 'manga-{plate}-{ifu}-LOGCUBE_MAPS-*-0**.fits.gz'.format(**fillkwargs),
                              'loc': 'mangawork/manga/spectro/analysis/{drpver}/{dapver}/full/{plate}/{ifu}/'.format(**fillkwargs),
                              'single': 'manga-{plate}-{ifu}-LOGCUBE_MAPS-NONE-003.fits.gz'.format(**fillkwargs),
                              'count': 21},
                 'mangadap5': {'files': 'manga-{plate}-{ifu}-*-SPX-GAU-MILESHC.fits.gz'.format(**fillkwargs),
                               'loc': 'mangawork/manga/spectro/analysis/{drpver}/{dapver}/*/{plate}/{ifu}/'.format(**fillkwargs),
                               'single': 'manga-{plate}-{ifu}-MAPS-SPX-GAU-MILESHC.fits.gz'.format(**fillkwargs),
                               'count': 2},
                 'mangacube': {'files': 'manga-{plate}-{ifu}-LOGCUBE.fits.gz'.format(**fillkwargs),
                               'loc': 'mangawork/manga/spectro/redux/{drpver}/{plate}/stack/'.format(**fillkwargs),
                               'single': 'manga-{plate}-{ifu}-LOGCUBE.fits.gz'.format(**fillkwargs),
                               'count': 1}
                 }
    return (request.param, data_dict[request.param])


@pytest.fixture()
def path():
    ''' Fixture to create a generic Path object '''
    path = Path()
    yield path
    path = None


@pytest.fixture(scope='function')
def rsync():
    ''' fixture to create generic rsync object '''
    rsync = RsyncAccess(label='test_rsync')
    rsync.remote()
    yield rsync

    # teardown
    rsync.reset()
    rsync = None


@pytest.fixture(scope='function')
def rsync_add(rsync, data, init_manga_survey):
    ''' fixture to add data to an rsync object '''
    name, paths = data
    rsync.add(name, **init_manga_survey.rsync_kwargs)
    rsync.location = paths['loc']
    yield rsync


@pytest.fixture(scope='function')
def rsync_set(rsync_add, data):
    ''' fixture to set the stream of an rsync object '''
    name, paths = data
    rsync_add.location = os.path.join(paths['loc'].replace('*', 'SPX-GAU-MILESHC'), paths['single'])
    rsync_add.count = paths['count']
    rsync_add.set_stream()
    yield rsync_add


