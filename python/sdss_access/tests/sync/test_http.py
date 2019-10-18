# !/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Filename: test_http.py
# Project: sync
# Author: Brian Cherinka
# Created: Monday, 16th September 2019 2:51:23 pm
# License: BSD 3-clause "New" or "Revised" License
# Copyright (c) 2019 Brian Cherinka
# Last Modified: Monday, 16th September 2019 3:08:02 pm
# Modified By: Brian Cherinka


from __future__ import print_function, division, absolute_import


class TestHttp(object):

    def test_http(self, http, datapath):
        name = http.release.lower() if http.release and 'DR' in http.release else datapath['work']
        path = http.url(datapath['name'], **datapath['params'])
        assert datapath['location'] in path
        assert 'https://data.sdss.org' in path
        assert name in path
