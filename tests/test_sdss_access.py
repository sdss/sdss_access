#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Filename: test_sdss_access.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

from __future__ import annotations

import sdss_access


def test_sdss_access():
    """Basic test for sdss_access package."""

    assert sdss_access.__version__ is not None
