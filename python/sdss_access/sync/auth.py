from netrc import netrc

""" add the following username and password to your ~/.netrc file
    and remember to chmod 600 ~/.netrc

machine data.sdss.org
    login sdss
    password ***-******
"""

class Auth:

    def __init__(self, public=False):
        if public: self.netrc = None
        else:
            try: self.netrc = netrc()
            except: self.netrc = None

    def set_username(self, username=None):
        self.username = username

    def set_password(self, password=None):
        self.password = password

    def ready(self):
        return self.username and self.password

    def set_host(self, host='data.sdss.org'):
        if self.netrc:
            authenticators = self.netrc.authenticators(host)
            self.set_username(authenticators[0])
            self.set_password(authenticators[2])
        else:
            self.set_username()
            self.set_password()
