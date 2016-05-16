from netrc import netrc

""" add the following username and password to your ~/.netrc file
    and remember to chmod 600 ~/.netrc

machine data.sdss.org
    login sdss
    password ***-******
"""

class Auth:

    def __init__(self, host=None, public=False, verbose=False):
        self.public = public
        self.verbose = verbose
        self.set_host(host=host)
        self.set_netrc()
        
    def set_netrc(self):
        try: self.netrc = netrc() if not self.public else None
        except: self.netrc = None

    def set_host(self, host=None):
        self.host = host

    def set_username(self, username=None):
        self.username = username

    def set_password(self, password=None):
        self.password = password

    def ready(self):
        return self.username and self.password

    def load(self):
        if self.host and self.netrc:
            authenticators = self.netrc.authenticators(self.host)
            self.set_username(authenticators[0])
            self.set_password(authenticators[2])
            if self.verbose: print "authentication for host=%r set for username=%r " % (self.host,self.username)
        else:
            self.set_username()
            self.set_password()
