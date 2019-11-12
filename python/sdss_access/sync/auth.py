from __future__ import absolute_import, division, print_function, unicode_literals
from six.moves import input
from sdss_access import is_posix
from os.path import join
from os import environ


class Auth(object):

    def __init__(self, netloc=None, public=False, verbose=False):
        self.public = public
        self.verbose = verbose
        self.set_netloc(netloc=netloc)
        self.set_netrc()

    def set_netrc(self):
        """ add the following username and password to your ~/.netrc file
            and remember to chmod 600 ~/.netrc

            machine data.sdss.org
            login sdss
            password ***-******

            Windows: recommending _netrc following
            https://stackoverflow.com/questions/6031214/git-how-to-use-netrc-file-on-windows-to-save-user-and-password
        """
        try:
            from netrc import netrc
        except Exception as e:
            netrc = None
            if self.verbose:
                print("SDSS_ACCESS> AUTH NETRC: %r" % e)
        if netrc:
            file = join(environ['HOME'], "_netrc") if not is_posix else None
            try:
                self.netrc = netrc(file) if not self.public else None
            except Exception as e:
                print("SDSS_ACCESS> Error %r" % e)
        else:
            self.netrc = None

    def set_netloc(self, netloc=None):
        self.netloc = netloc

    def set_username(self, username=None, inquire=False):
        self.username = input("user [sdss]: ") or "sdss" if inquire else username

    def set_password(self, password=None, inquire=False):
        try:
            from getpass import getpass
            self.password = getpass("password: ") if inquire else password
        except Exception as e:
            if self.verbose:
                print("SDSS_ACCESS> AUTH PASSWORD: %r" % e)
            self.password = None

    def ready(self):
        return self.username and self.password

    def load(self):
        if self.netloc and self.netrc:
            authenticators = self.netrc.authenticators(self.netloc)
            if authenticators and len(authenticators) == 3:
                self.set_username(authenticators[0])
                self.set_password(authenticators[2])
                if self.verbose:
                    print("authentication for netloc=%r set for username=%r " % (self.netloc, self.username))
            else:
                if self.verbose:
                    print("cannot find %r in ~/.netrc" % self.netloc)
                self.set_username()
                self.set_password()
        else:
            self.set_username()
            self.set_password()
