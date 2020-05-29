# !usr/bin/env python2
# -*- coding: utf-8 -*-
#
# Licensed under a 3-clause BSD license.
#
# @Author: Brian Cherinka
# @Date:   2017-03-24 12:22:07
# @Last modified by:   Brian Cherinka
# @Last Modified time: 2018-07-08 15:47:42

from __future__ import print_function, division, absolute_import
import os
import pytest
from sdss_access import Access, AccessError
from sdss_access.sync import RsyncAccess


class TestRsync(object):

    def test_rsync(self, radd, expdata):
        assert radd.remote_base == expdata['base']
        assert radd.base_dir == os.environ.get("SAS_BASE_DIR") + '/'

    def test_get_locations(self, rstream, expdata):
        location = rstream.get_locations()[0]
        assert location == expdata['location']

    def test_get_paths(self, rstream, expdata):
        path = rstream.get_paths()[0]
        assert path == expdata['destination']

    @pytest.mark.slow
    def test_commit(self, monkeypatch, tmpdir, rsync):
        sasdir = tmpdir.mkdir("sas")
        monkeypatch.setenv("SAS_BASE_DIR", str(sasdir))

        # need to replant tree since rsync is a session level fixture
        rsync.replant_tree()
        rsync.add('drpall', drpver='v2_4_3')
        rsync.set_stream()
        rsync.commit()

        path = rsync.get_paths()[0]
        print('path', path)
        assert os.path.exists(path) is True
        assert os.path.isfile(path) is True

    @pytest.mark.parametrize('tree_ver, exp', [('sdsswork', 'work'), ('dr15', 'dr15'),
                                               ('dr13', 'dr13'), ('mpl8', 'work')])
    def test_release_from_module(self, monkeypatch, tree_ver, exp, datapath):
        monkeypatch.setenv('TREE_VER', tree_ver)
        rsync = RsyncAccess()
        rsync.remote()
        rsync.add(datapath['name'], **datapath['params'])
        loc = rsync.initial_stream.task[0]['location']
        assert rsync.release == tree_ver
        assert exp in loc


class TestRsyncFails(object):

    def test_access_svn_fail(self):
        with pytest.raises(AccessError) as cm:
            access = Access()
            access.remote()
            access.add('mangapreimg', designid=8405, designgrp='D0084XX', mangaid='1-42007')
        assert 'Rsync/Curl Access not allowed for svn paths.  Please use HttpAccess.' in str(cm.value)


class TestStream(object):
    def test_initial_stream(self, radd, inittask):
        task = radd.initial_stream.task
        assert task == inittask

    def test_final_stream(self, rstream, finaltask):
        task = rstream.stream.task
        assert task == finaltask
