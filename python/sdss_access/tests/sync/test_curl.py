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

 
class TestCurlAdd(object):

    def test_curl_add_link(self, curl_add):
        task = curl_add.initial_stream.task[0]
        assert curl_add.location in task['location']


class TestCurlStream(object):

    def test_curl_setstream_task(self, curl_set):
        tasks = curl_set.stream.task
        locations = curl_set.get_locations()
        assert curl_set.location in locations
