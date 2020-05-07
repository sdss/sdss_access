# !/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Filename: utils.py
# Project: path
# Author: Brian Cherinka
# Created: Thursday, 23rd April 2020 1:24:14 pm
# License: BSD 3-clause "New" or "Revised" License
# Copyright (c) 2020 Brian Cherinka
# Last Modified: Thursday, 23rd April 2020 1:24:15 pm
# Modified By: Brian Cherinka


from __future__ import print_function, division, absolute_import

from tree import Tree
from tree.changelog import compute_changelog as compute_path_changes


def compute_changelog(new, old, pprint=None, to_list=None):
    ''' Compute the difference between two Tree PATH sections

    Compares two tree PATH ini sections from the given environment
    configurations and returns  adictionary with keys `new`, and `updated`,
    indicating newly added paths, and any paths that have been modified
    from the last release.  Accepts either string names of config
    files, e.g. "dr16" and "dr15", or the preloaded `Tree` configs, e.g.
    `Tree(config='dr16')`.

    Parameters:
        new (str|Tree):
            The new tree enviroment to compare
        old (str|Tree):
            The old tree environment to compare
        pprint (bool):
            If True, returns a single joined string for printing. Default is False.
        to_list (bool):
            If True, returns a list of strings formatted for printing. Default is False.

    Returns:
        A dictionary of relevant changes between the two releases
    '''

    diffs = compute_path_changes(new, old, pprint=pprint, paths_only=True, to_list=to_list)

    return diffs


def get_path_templates(name, public=None):
    ''' Return the path templates for all releases

    Produces a dictionary of path templates for a given
    path name for all releases.  Set public keyword to toggle only
    public data releases (DRs).

    Parameters:
        name (str):
            The sdss_access path name
        public (bool):
            If True, selects only public data releases

    Returns:
        A dictionary of the path template per release
    '''
    releases = Tree.get_available_releases(public=public)
    versions = {}
    for release in reversed(releases):
        release = 'sdsswork' if 'WORK' in release else release
        tree = Tree(config=release)
        versions[release] = tree.paths.get(name, None)
    return versions


def get_available_releases(public=None):
    ''' Get the available releases

    Parameters:
        public (bool):
            If True, only return public data releases
    '''
    return Tree.get_available_releases(public=public)
