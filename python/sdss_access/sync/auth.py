from netrc import netrc

""" add the following username and password to your ~/.netrc file
    and remember to chmod 600 ~/.netrc

machine data.sdss.org
    login sdss
    password ***-******
"""

class Auth:

    def __init__(self):
        self.netrc = netrc()

    def set_host(self, host='data.sdss.org'):
        self.username, account, self.password = self.netrc.authenticators(host)

