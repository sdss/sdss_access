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


class TestStream(object):
    def test_initial_stream(self, radd, exptask):
        task = radd.initial_stream.task
        assert task == exptask

    def test_final_stream(self, rstream, exptask):
        initial_task = rstream.initial_stream.task
        task = rstream.stream.task
        assert task == exptask
        assert task == initial_task
