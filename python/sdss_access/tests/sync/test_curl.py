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

    def test_curl_add_link(self, curl_add):
        task = curl_add.initial_stream.task[0]
        assert curl_add.location in task['location']


class TestRsyncStream(object):

    def test_curl_setstream_task(self, curl_set):
        tasks = curl_set.stream.task
        locations = curl_set.get_locations()
        assert curl_set.location in locations
