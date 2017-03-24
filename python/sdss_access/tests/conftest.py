# !usr/bin/env python2
# -*- coding: utf-8 -*-
#
# Licensed under a 3-clause BSD license.
#
# @Author: Brian Cherinka
# @Date:   2017-03-24 12:22:30
# @Last modified by:   Brian Cherinka
# @Last Modified time: 2017-03-24 15:41:18

from __future__ import print_function, division, absolute_import
import os
import pytest

from sdss_access import RsyncAccess


@pytest.fixture(scope='function')
def rsync(request):
    rsync = RsyncAccess(label='test_rsync')
    rsync.remote()

    def teardown():
        rsync.reset()
        rsync = None

    return rsync
