# !usr/bin/env python
# -*- coding: utf-8 -*-
#
# Licensed under a 3-clause BSD license.
#
# @Author: Brett Andrews
# @Date:   2017-04-11


from __future__ import print_function, division, absolute_import

import pytest

from sdss_access.sync.auth import Auth


def test_set_username_interactively():
    """If authentication via `.netrc` file fails, then test for interactive prompt.

    The interactive prompt raises an IOError (merged into OSError in Python 3.3), which this test
    expects.
    """
    with pytest.raises((IOError, OSError)):
        auth = Auth(netloc='data.sdss.org', public=False)
        auth.set_username(inquire=True)
