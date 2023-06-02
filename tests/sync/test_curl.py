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


class TestCurl(object):

    def test_curl(self, curl, datapath):
        name = curl.release.lower() if curl.release and 'dr' in curl.release else datapath['work']
        path = curl.url(datapath['name'], **datapath['params'])
        assert datapath['location'] in path
        assert f'https://{datapath["url"]}' in path
        assert name in path

