from ._version import get_versions

try:
    __version__ = get_versions()['version']
    del get_versions
except Exception:
    __version__ = '0.0.0-unknown'
