# !usr/bin/env python2
# -*- coding: utf-8 -*-
#
# Licensed under a 3-clause BSD license.
#
# @Author: Brian Cherinka
# @Date:   2017-03-24 12:22:07
# @Last modified by:   Brian Cherinka
# @Last Modified time: 2017-03-24 15:55:24

from __future__ import print_function, division, absolute_import
import os


class TestRsyncAdd(object):

    def test_rsync_add_symlink(self, rsync):
        rsync.add('mangadefault', drpver='v1_5_1', dapver='1.1.1', plate='8485', ifu='1901')
        name = 'mangadap-8485-1901-default.fits.gz'
        path = os.path.join('mangawork/manga/spectro/analysis/v1_5_1/1.1.1/default/8485/', name)
        task = rsync.initial_stream.task[0]
        assert path in task['location']

    def test_rsync_add_multireal(self, rsync):
        rsync.add('mangamap', plate='8485', drpver='v1_5_1', dapver='1.1.1', ifu='1901', mode='*', n='**', bintype='*')
        name = 'manga-8485-1901-LOGCUBE_MAPS-*-0**.fits.gz'
        path = os.path.join('mangawork/manga/spectro/analysis/v1_5_1/1.1.1/full/8485/1901/', name)
        task = rsync.initial_stream.task[0]
        assert path in task['location']


class TestRsyncStream(object):

    def test_rsync_setstream_symlink(self, rsync):
        rsync.add('mangadefault', drpver='v1_5_1', dapver='1.1.1', plate='8485', ifu='1901')
        name = 'mangadap-8485-1901-default.fits.gz'
        path = os.path.join('mangawork/manga/spectro/analysis/v1_5_1/1.1.1/default/8485/', name)
        rsync.set_stream()
        tasks = rsync.stream.task
        task = tasks[0]
        assert path in task['location']
        assert len(tasks) == 1

    def test_rsync_setstream_multireal(self, rsync):
        rsync.add('mangamap', plate='8485', drpver='v1_5_1', dapver='1.1.1', ifu='1901', mode='*', n='**', bintype='*')
        name = 'manga-8485-1901-LOGCUBE_MAPS-NONE-003.fits.gz'
        path = os.path.join('mangawork/manga/spectro/analysis/v1_5_1/1.1.1/full/8485/1901/', name)
        rsync.set_stream()
        tasks = rsync.stream.task
        task = tasks[0]
        assert path in task['location']
        assert len(tasks) == 21


