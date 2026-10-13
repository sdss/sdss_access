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
import pytest

class TestCurl(object):

    def test_curl(self, curl, datapath):
        name = curl.release.lower() if curl.release and 'dr' in curl.release else datapath['work']
        path = curl.url(datapath['name'], **datapath['params'])
        assert datapath['location'] in path
        assert f'https://{datapath["url"]}' in path
        assert name in path

    @pytest.mark.parametrize('input_type', ['filepath', 'url', 'location'])
    def test_add_files(self, curl, expdata, input_type):

        # hack the source for curl
        source = (expdata['source'].replace('rsync://sdss5@dtn.sdss.org/',
                                           'https://data.sdss5.org/sas/')
                  .replace('rsync://dtn.sdss.org/', 'https://data.sdss.org/sas/'))

        if input_type == 'filepath':
            path = expdata.get('destination')
        elif input_type == 'url':
            path = source
        else:
            path = expdata.get('location')

        expout = {'sas_module': expdata['sas_module'], 'location': expdata['location'],
                  'source': source, 'destination': expdata['destination'],
                  'exists': None}

        curl.add_file(path, input_type=input_type)
        task = curl.initial_stream.task[0]
        assert task == expout

    @pytest.mark.parametrize('followsym', [True, False])
    def test_symlink(self, cadd, followsym):
        """ test the follow symlink option is added or not """
        cmd = cadd._get_stream_command(follow_symlinks=followsym)
        if followsym:
            assert "-sSRKL" in cmd
        else:
            assert "-sSRK" in cmd
