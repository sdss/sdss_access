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
        assert os.path.exists(path) is True
        assert os.path.isfile(path) is True

    @pytest.mark.parametrize('tree_ver, exp', [('dr15', 'dr15'),
                                               ('dr13', 'dr13')])
    def test_release_from_module(self, monkeypatch, tree_ver, exp):
        monkeypatch.setenv('TREE_VER', tree_ver)
        rsync = RsyncAccess()
        rsync.remote()
        rsync.add('mangacube', ifu=1901, wave='LOG', plate=8485, drpver='v3_1_1')
        loc = rsync.initial_stream.task[0]['sas_module']
        assert rsync.release == tree_ver
        assert exp in loc

    def test_remote_compression(self):
        """ test we can find the correct file when the remote file is compressed """
        rsync = RsyncAccess(release='ipl3')
        rsync.remote()

        # template path is not compressed
        ff = rsync.templates["mwmAllStar"]
        assert ff.endswith('summary/mwmAllStar-{v_astra}.fits')

        # remote source is fully resolved path
        rsync.add("mwmAllStar", v_astra="0.5.0")
        rsync.set_stream()
        source = rsync.stream.task[0]['source']
        assert source.endswith('0.5.0/summary/mwmAllStar-0.5.0.fits.gz')

    @pytest.mark.parametrize('input_type', ['filepath', 'url', 'location'])
    def test_add_files(self, rsync, expdata, inittask, input_type):

        if input_type == 'filepath':
            path = expdata.get('destination')
        elif input_type == 'url':
            path = expdata.get('source')
        else:
            path = expdata.get('location')

        rsync.add_file(path, input_type=input_type)
        task = rsync.initial_stream.task[0]
        assert task == inittask[0]


class TestRsyncFails(object):

    def test_access_svn_fail(self):
        with pytest.raises(AccessError) as cm:
            access = Access(release='dr17')
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


