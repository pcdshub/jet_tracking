from . import cam_utils  # noqa
from . import devices  # noqa
from . import jet_control  # noqa
from . import move_motor  # noqa
from ._version import get_versions

try:
    __version__ = get_versions()['version']
    del get_versions
except Exception:
    __version__ = '0.0.0-unknown'
