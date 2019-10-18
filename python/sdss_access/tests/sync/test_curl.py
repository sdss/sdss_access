# !usr/bin/env python2
# -*- coding: utf-8 -*-
#
# Licensed under a 3-clause BSD license.
#
# @Author: Michael Talbot
# @Date:   2019-08-7 12:30:00
# @Last modified by:   Michael Talbot
# @Last Modified time: 2019-08-07 12:30:00

from __future__ import print_function, division, absolute_import
import os
import pytest


class TestCurl(object):

    def test_curl(self, cadd, expdata):
        assert cadd.remote_base == expdata['base']
        assert cadd.base_dir == os.environ.get("SAS_BASE_DIR") + '/'

    def test_get_locations(self, cstream, expdata):
        location = cstream.get_locations()[0]
        assert location == expdata['location']

    def test_get_paths(self, cstream, expdata):
        path = cstream.get_paths()[0]
        assert path == expdata['destination']

    @pytest.mark.slow
    def test_commit(self, monkeypatch, tmpdir, curl):
        sasdir = tmpdir.mkdir("sas")
        monkeypatch.setenv("SAS_BASE_DIR", str(sasdir))

        # need to replant tree since curl is a session level fixture
        curl.replant_tree()
        curl.add('drpall', drpver='v2_4_3')
        curl.set_stream()
        curl.commit()

        path = curl.get_paths()[0]
        print('path', path)
        assert os.path.exists(path) is True
        assert os.path.isfile(path) is True


class TestStream(object):
    def test_initial_stream(self, cadd, inittask):
        task = cadd.initial_stream.task
        assert task == inittask

    def test_final_stream(self, cstream, finaltask):
        task = cstream.stream.task
        assert task == finaltask
