import logging

from jet_tracking.signals import Signals

logger = logging.getLogger(__name__)


def test_signals_smoke():
    logger.debug("test_signals")
    Signals()
