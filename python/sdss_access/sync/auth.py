from __future__ import absolute_import, division, print_function, unicode_literals
from six.moves import input
from sdss_access import is_posix
from sdss_access.path import AccessError
from os.path import join
from os import environ


class Auth(object):
    ''' class for setting up SAS authenticaton for SDSS users '''

    def __init__(self, netloc=None, public=False, verbose=False):
        self.public = public
        self.verbose = verbose
        self.username = None
        self.password = None
        self.set_netloc(netloc=netloc)
        self.set_netrc()

    def set_netrc(self):
        """ add the following username and password to your ~/.netrc file
            and remember to chmod 600 ~/.netrc

            For SDSS-IV access:
            machine data.sdss.org
            login sdss
            password ***-******

            For SDSS-V access:
            machine data.sdss5.org
            login sdss5
            password *******-*

            Windows: recommending _netrc following
            https://stackoverflow.com/questions/6031214/git-how-to-use-netrc-file-on-windows-to-save-user-and-password
        """
        # set blank netrc
        self.netrc = None

        # if public do nothing
        if self.public:
            return

        # try to get the netrc file
        try:
            from netrc import netrc
        except Exception as e:
            netrc = None
            if self.verbose:
                print("SDSS_ACCESS> AUTH NETRC: {0}".format(e))

        if netrc:
            netfile = join(environ['HOME'], "_netrc") if not is_posix else None
            try:
                self.netrc = netrc(netfile)
            except FileNotFoundError as e:
                raise AccessError("No netrc file found. Please create one. {0}".format(e))

    def set_netloc(self, netloc=None):
        ''' sets the url domain location '''
        self.netloc = netloc

    def set_username(self, username=None, inquire=None):
        ''' sets the authentication username

        Parameters:
            username: str
                The username for SDSS SAS access
            inquire: bool
                If True, prompts for input of username.
        '''
        self.username = input("user [sdss]: ") or "sdss" if inquire else username

    def set_password(self, password=None, inquire=None):
        ''' sets the authentication password

        Parameters:
            password: str
                The password for SDSS SAS access
            inquire: bool
                If True, prompts for input of password.
        '''
        try:
            from getpass import getpass
            self.password = getpass("password: ") if inquire else password
        except Exception as e:
            if self.verbose:
                print("SDSS_ACCESS> AUTH PASSWORD: {0}".format(e))
            self.password = None

    def ready(self):
        return self.username and self.password

    def load(self):
        ''' Sets the username and password from the local netrc file '''
        if self.netloc and self.netrc:
            authenticators = self.netrc.authenticators(self.netloc)
            if authenticators and len(authenticators) == 3:
                self.set_username(authenticators[0])
                self.set_password(authenticators[2])
                if self.verbose:
                    print("authentication for netloc={0} set for username={1}".format(self.netloc, self.username))
            else:
                if self.verbose:
                    print("cannot find {0} in ~/.netrc".format(self.netloc))
                self.set_username()
                self.set_password()
        else:
            self.set_username()
            self.set_password()


class AuthMixin(object):
    ''' Mixin class to provide authentication method to other classes '''

    def set_auth(self, username=None, password=None, inquire=True):
        ''' Set the authentication

        Parameters:
            username: str
                The username for SDSS SAS access
            password: str
                The password for SDSS SAS access
            inquire: bool
                If True, prompts for input of username/password.
        '''
        self.auth = Auth(public=self.public, netloc=self.netloc, verbose=self.verbose)
        self.auth.set_username(username)
        self.auth.set_password(password)

        # if public then exit
        if self.public:
            return

        # try to load the username and password
        if not self.auth.ready():
            self.auth.load()

        # if still not ready then prompt for username and password
        if not self.auth.ready():
            self.auth.set_username(inquire=inquire)
            self.auth.set_password(inquire=inquire)
