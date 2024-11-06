# !usr/bin/env python2
# -*- coding: utf-8 -*-
#
# Licensed under a 3-clause BSD license.
#
# @Author: Brian Cherinka
# @Date:   2017-03-24 12:22:30
# @Last modified by:   Michael Talbot
# @Last Modified time: 2019-08-07 12:30:00

from __future__ import print_function, division, absolute_import
import glob
import gzip
import importlib
import os
import pytest
import yaml
import contextlib
import shutil

import tree.tree as treemod
from sdss_access import RsyncAccess, HttpAccess, CurlAccess
from sdss_access.path import Path

pytest_plugins = 'sphinx.testing.fixtures'
collect_ignore = ["roots"]


# PYTEST MODIFIERS
# -----------------
def pytest_addoption(parser):
    """Add new options"""
    # run slow tests
    parser.addoption('--runslow', action='store_true', default=False, help='Run slow tests.')


def pytest_runtest_setup(item):
    """Skip slow tests."""
    if 'slow' in item.keywords and not item.config.getoption('--runslow'):
        pytest.skip('Requires --runslow option to run.')


@pytest.fixture()
def path():
    ''' Fixture to create a generic Path object '''
    path = Path(release='dr17')
    path.replant_tree()
    yield path
    path = None


# read in test data parameters and also get paths
def get_data():
    ''' Retrieves the test data from the paths.yaml file '''

    with open(os.path.join(os.path.dirname(__file__), 'data/paths.yaml')) as f:
        data = yaml.load(f, Loader=yaml.SafeLoader)
    return data

data = get_data()
paths = data.get('paths')


@pytest.fixture(scope='session', params=paths)
def datapath(request):
    ''' parametrizes over the paths in test data'''
    return request.param


@pytest.fixture(scope='session')
def expdata(datapath):
    ''' fixture to yield expected source data based on test data '''
    remote = data.get('remote_base')
    # remote base
    base = remote['work'] if 'work' in datapath['release'] else remote['public']
    # sas_module; a work or DR directory
    sas_module = datapath['work'] if 'work' in datapath['release'] else datapath['release'].lower()
    # file location
    location = datapath['location']
    # full source file location
    source = os.path.join(base, sas_module, location)
    # full final file location
    destination = os.path.normpath(os.path.join(os.getenv('SAS_BASE_DIR'), sas_module, location))
    # combined dict
    result = {'name': datapath['name'], 'params': datapath['params'], 'base': base,
              'sas_module': sas_module, 'location': location, 'source': source,
              'destination': destination, 'release': datapath['release'].lower()}
    yield result
    result = None


@pytest.fixture(scope='session')
def inittask(expdata):
    ''' fixture to yield expected initial stream task based on test data '''

    task = [{'sas_module': expdata['sas_module'], 'location': expdata['location'],
             'source': expdata['source'], 'destination': expdata['destination'], 'exists': None}]
    yield task
    task = None


@pytest.fixture(scope='session')
def finaltask(expdata):
    ''' fixture to yield expected final stream task based on test data '''

    task = [{'sas_module': expdata['sas_module'], 'location': expdata['location'],
             'source': expdata['source'], 'destination': expdata['destination'], 'exists': None}]
    yield task
    task = None


@pytest.fixture(scope='session')
def rsync(datapath):
    ''' fixture to create generic rsync object - parametrized by release '''

    rsync = RsyncAccess(label='test_rsync', release=datapath['release'])
    rsync.remote()
    yield rsync
    # teardown
    rsync.reset()
    rsync = None


@pytest.fixture(scope='session')
def radd(rsync, expdata):
    ''' fixture to add a path to an rsync object '''
    rsync.add(expdata['name'], **expdata['params'])
    yield rsync
    rsync.reset()


@pytest.fixture(scope='session')
def rstream(radd):
    ''' fixture to set the stream for an parametrized rsync object '''
    radd.set_stream()
    yield radd
    radd.reset()


@pytest.fixture(scope='session')
def http(datapath):
    http = HttpAccess(release=datapath['release'])
    yield http
    http = None


@pytest.fixture(scope='session')
def curl(datapath):
    ''' fixture to create generic curl object - parametrized by release '''

    curl = CurlAccess(label='test_curl', release=datapath['release'])
    curl.remote()
    yield curl
    # teardown
    curl.reset()
    curl = None


@pytest.fixture(scope='session')
def cadd(curl, expdata):
    ''' fixture to add a path to an curl object '''
    curl.add(expdata['name'], **expdata['params'])
    yield curl


@pytest.fixture(scope='session')
def cstream(cadd):
    ''' fixture to set the stream for an parametrized curl object '''
    cadd.set_stream()
    yield cadd


@pytest.fixture()
def monkeysas(tmpdir, monkeypatch, path):
    ''' fixture to monkeypatch the sas_base_dir '''
    orig = os.getenv("SAS_BASE_DIR")
    tmppath = tmpdir / 'sas'
    os.makedirs(tmppath, exist_ok=True)
    monkeypatch.setenv('SAS_BASE_DIR', str(tmppath))
    path.replant_tree()
    yield
    os.environ["SAS_BASE_DIR"] = orig
    path.replant_tree()


@pytest.fixture()
def copydata(tmpdir, request):
    ''' fixture to copy a file into a temporary directory '''
    srcpath = os.path.join(os.getenv("SAS_BASE_DIR"), request.param)
    # skip the test if no real data exists to copy
    if not os.path.exists(srcpath):
        pytest.skip('file does not exist cannot copy')
    sasdir = tmpdir / 'sas'
    destpath = sasdir / request.param
    os.makedirs(os.path.dirname(destpath), exist_ok=True)
    shutil.copy(srcpath, destpath)
    yield destpath


@pytest.fixture()
def copymulti(tmpdir, request):
    ''' Fixture to copy multiple files into a temporary directory '''
    srcpath = os.path.join(os.getenv("SAS_BASE_DIR"), request.param)
    files = glob.glob(srcpath)
    if not files:
        pytest.skip('Files do not exist, cannot copy')
    for item in files:
        loc = item.split(os.getenv("SAS_BASE_DIR") + '/')[-1]
        sasdir = tmpdir / 'sas'
        destpath = sasdir / loc
        os.makedirs(os.path.dirname(destpath), exist_ok=True)
        shutil.copy(item, destpath)


@contextlib.contextmanager
def gzuncompress(filename):
    ''' Context manager than gunzips a file temporarily. '''
    import pathlib
    pp = pathlib.Path(filename)
    decompfile = pp.parent / pp.stem
    with gzip.open(filename, 'rb') as f_in:
        with open(decompfile, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    os.remove(filename)
    yield


@contextlib.contextmanager
def gzcompress(filename):
    ''' Context manager than gzips a file temporarily. '''
    compfile = filename + '.gz'
    with open(filename, 'rb') as f_in:
        with gzip.open(compfile, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    os.remove(filename)
    yield


@pytest.fixture()
def monkeyhome(monkeypatch, tmp_path):
    ''' monkeypatch the HOME directory '''
    path = (tmp_path / 'tmp').mkdir()
    monkeypatch.setenv("HOME", str(path))


@pytest.fixture()
def monkeysdss5(monkeypatch):
    monkeypatch.setenv('ALLWISE_DIR', '/tmp/allwise')
    monkeypatch.setenv('EROSITA_DIR', '/tmp/erosita')
    monkeypatch.setenv('ROBOSTRATEGY_DATA', '/tmp/robodata')
    importlib.reload(treemod)