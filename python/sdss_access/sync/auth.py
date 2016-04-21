from netrc import netrc

""" add the following username and password to your ~/.netrc file
    and remember to chmod 600 ~/.netrc

machine data.sdss.org
    login sdss
    password ***-******
"""

class Auth:

    def __init__(self):
        try: self.netrc = netrc()
        except: self.netrc = None

    def set_host(self, host='data.sdss.org'):
        if self.netrc: self.username, account, self.password = self.netrc.authenticators(host)
        else: self.username, self.password = None,None

