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


class TestRsyncAdd(object):

    def test_rsync_add_link(self, rsync_add):
        task = rsync_add.initial_stream.task[0]
        assert rsync_add.location in task['location']


class TestRsyncStream(object):

    def test_rsync_setstream_task(self, rsync_set):
        tasks = rsync_set.stream.task
        locations = rsync_set.get_locations()
        assert rsync_set.location in locations
