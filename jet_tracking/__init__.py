from ._version import get_versions
__version__ = get_versions()['version']
del get_versions


from . import jet_control  # noqa
from . import devices  # noqa
from . import cam_utils  # noqa
from . import move_motor  # noqa
