import pkg_resources

try:
    __version__ = pkg_resources.get_distribution(__name__).version
except:
    __version__ = 'unknown'

# General module methods
def flipdict(d):
    ''' switch keys and values, so that all values are keys in a new dict '''
    return dict(zip(*list(reversed(zip(*[(k, v) for k in d for v in d[k]])))))

