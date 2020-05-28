# !usr/bin/env python
# -*- coding: utf-8 -*-
#
# Licensed under a 3-clause BSD license.
#
# @Author: Brett Andrews
# @Date:   2017-04-11


from __future__ import print_function, division, absolute_import

import importlib
import six.moves
import pytest

import sdss_access
from sdss_access.sync.auth import Auth, AuthMixin
from sdss_access.path import AccessError


class TestAuth(object):

    def test_nonetrc_fails(self, monkeyhome):
        ''' test raise error when no netrc present '''
        with pytest.raises(AccessError) as cm:
            Auth()
        assert 'No netrc file found. Please create one.' in str(cm.value)

    def test_nonetrc_public_pass(self, monkeyhome):
        ''' test public access does not fail when no netrc '''
        auth = Auth(public=True)
        assert auth.public is True
        assert auth.ready() is None
        assert auth.netrc is None

    @pytest.mark.parametrize('netloc', [('data.sdss.org'), ('dtn01.sdss.org')])
    def test_setnetloc(self, netloc):
        ''' test setting a url domain location '''
        auth = Auth(public=True, netloc=netloc)
        assert auth.netloc == netloc

    def test_auth_goodnetrc(self):
        ''' test for a netrc loaded '''
        auth = Auth()
        assert auth.netrc is not None
        assert 'data.sdss.org' in auth.netrc.hosts.keys()

    @pytest.mark.parametrize('public', [(True), (False)])
    def test_auth_defaultuser(self, public):
        ''' test auth load default user '''
        auth = Auth(netloc='data.sdss.org', public=public)
        auth.load()
        if public:
            assert auth.username is None
        else:
            assert auth.username == auth.netrc.authenticators('data.sdss.org')[0]

    def test_auth_setuserpass(self):
        ''' test set userpass '''
        auth = Auth(netloc='data.sdss.org')
        assert auth.username is None
        assert auth.password is None
        auth.set_username('testuser')
        auth.set_password('testpass')
        assert auth.username == 'testuser'
        assert auth.password == 'testpass'

    @pytest.mark.parametrize('prompt, exp', [('blah', 'blah'), (None, 'sdss')])
    def test_user_inquire(self, monkeypatch, prompt, exp):
        ''' test username input prompt '''
        # mock the six.moves.input
        def mockinput(value):
            return prompt

        monkeypatch.setattr(six.moves, 'input', mockinput)
        # reload the auth module
        importlib.reload(sdss_access.sync.auth)
        from sdss_access.sync.auth import Auth

        # run the test
        auth = Auth()
        auth.set_username(inquire=True)
        assert auth.username == exp


class TmpAccess(AuthMixin, object):
    def __init__(self, public=None, netloc=None, verbose=None):
        self.public = public
        self.netloc = netloc
        self.verbose = verbose


class TestAuthMixin(object):

    def test_set_auth(self):
        ''' test the set_auth method '''
        ta = TmpAccess(netloc='data.sdss.org')
        ta.set_auth()
        assert ta.netloc == 'data.sdss.org'
        assert ta.auth is not None
        assert ta.auth.netloc == 'data.sdss.org'
        assert ta.auth.username == 'sdss'

    def test_set_auth_public(self):
        ''' test the public option '''
        ta = TmpAccess(netloc='data.sdss.org', public=True)
        ta.set_auth()
        assert ta.auth is not None
        assert ta.auth.public is True
        assert ta.auth.username is None

