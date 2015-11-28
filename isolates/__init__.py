import pkg_resources
import socket
import urllib
from email.mime.text import MIMEText
from subprocess import Popen, PIPE
from shutil import rmtree
from tempfile import mkdtemp

# GENERAL MODULE CLASSES
class TemporaryDirectory(object):
    """Create and return a temporary directory.  This has the same
    behavior as mkdtemp but can be used as a context manager.  For
    example:
    
    >>> import os
    >>> tmpfile = 'file.ext'
    >>> with TemporaryDirectory() as tmpdir:
    ...    print "Was tmpdir created? %s"%os.path.exists(tmpdir)
    ...    os.chdir(tmpdir)
    ...    with open(tmpfile, 'w') as f:
    ...       f.write('Hello World!')
    ...    print "Was tmpfile created? %s"%os.path.exists(tmpfile)
    Was tmpdir created? True
    Was tmpfile created? True
    >>> print "Does tmpfile still exist? %s"%os.path.exists(tmpfile)
    Does tmpfile still exist? False
    >>> print "Does tmpdir still exist? %s"%os.path.exists(tmpdir)
    Does tmpdir still exist? False
    
    Upon exiting the context, the directory and everything contained
    in it are removed.
    This method is not implemented in python-2.7!
    """
    def __init__(self, suffix="", prefix="tmp", dir=None):
        self.name = None
        self.name = mkdtemp(suffix, prefix, dir)
    def __enter__(self):
        return self.name
    def cleanup(self, _warn=False):
        if self.name:
            try: rmtree(self.name)
            except: print('Could not remove %s'%self.name)
            else: self.name = None
    def __exit__(self, exc, value, tb):
        self.cleanup()

class openurl(object):
    ''' urllib library wrapper, to make it easier to use.
    >>> import urllib
    >>> with openurl('http://www.ncbi.nlm.nih.gov/sra/?term=ERX006651&format=text') as u:
    ...   for l in u:
    ...      print l.strip()
    '''
    def __init__(self, url):
        self.url = url
    def __enter__(self):
        self.u = urllib.urlopen(self.url)
        return self.u 
    def __exit__(self, type=None, value=None, traceback=None):
        self.u.close()
        self.u = None
    def __iter__(self):
        yield self.readline()
    def read(self):
        return self.u.read()
    def readline(self):
        return self.u.readline()
    def readlines(self):
        return self.u.readlines()

class mail_obj():
    '''
    >>> mail = mail_obj(['to_me@domain.com'], 'from_me@domain.com')
    >>> mail.send('Hello my subject!','Hello my body!')
    '''
    def __init__(self, recepients, sender, reply):
        self.to = recepients
        self.fr = sender
        self.rt = reply
    def send(self, subject, message):
        '''  '''
        msg = MIMEText(message)
        msg["To"] = ', '.join(self.to) if isinstance(self.to, list) else self.to
        msg["From"] = self.fr
        msg["Reply-To"] = self.rt
        msg["Subject"] = subject
        p = Popen(["sendmail -r %s %s"%(self.fr, ' '.join(self.to))],
                  shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        out, err = p.communicate(msg.as_string())
        p.wait()
    def test(self, subject, message):
        '''  '''
        msg = MIMEText(message)
        msg["To"] = ', '.join(self.to) if isinstance(self.to, list) else self.to
        msg["From"] = self.fr
        msg["Reply-To"] = self.rt
        msg["Subject"] = subject
        print("sendmail -r %s %s"%(self.fr, ' '.join(self.to)))
        print(msg.as_string())

# GENERAL MODULE FUNCTIONS
def flipdict(d):
    ''' switch keys and values, so that all values are keys in a new dict '''
    return dict(zip(*list(reversed(zip(*[(k, v) for k in d for v in d[k]])))))

def ceil(n):
    ''' compute the closest upper integer of a float '''
    return int(n) + (n%1 > 0)

# MAIN

# Set version
try:
    __version__ = pkg_resources.get_distribution(__name__).version
except:
    __version__ = 'unknown'

# Setup Mail Wrapper
if 'cbs.dtu.dk' in socket.getfqdn():
    mail = mail_obj(['mcft@cbs.dtu.dk'],
                    'mail-deamon@cbs.dtu.dk',
                    'cgehelp@cbs.dtu.dk')
elif 'computerome' in socket.getfqdn():
    mail = mail_obj(['mcft@cbs.dtu.dk'],
                    'mail-deamon@computerome.dtu.dk',
                    'cgehelp@cbs.dtu.dk')
else:
    mail = None
