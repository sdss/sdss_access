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


class TestStream(object):
    def test_initial_stream(self, radd, inittask):
        task = radd.initial_stream.task
        assert task == inittask

    def test_final_stream(self, rstream, finaltask):
        task = rstream.stream.task
        assert task == finaltask
