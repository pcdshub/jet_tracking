import logging

import bluesky.plan_stubs as bps
import bluesky.preprocessors as bpp
import bluesky.plans as bp

import numpy as np

logger = logging.getLogger(__name__)


class SignalLostError(Exception):
    """Raised when the signal is read lower than threshold"""
    pass


def wiggle(detectors, target_field, motor, step_size, per_step=None):
    """
    Wiggle the motor back and forth and sample values
    """
    per_step = per_step or bps.one_1d_step

    def sample_at_point(position):
        # Take a sample
        logger.debug("Sampling detectors at %r", motor.position)
        event = yield from per_step(detectors, motor, position)
        return (position, event[target_field])

    # Sample all of our points
    start_position = motor.position
    start_sample = yield from sample_at_point(start_position)
    first_sample = yield from sample_at_point(start_position + step_size)
    second_sample = yield from sample_at_point(start_position - step_size)

    return max(start_sample, first_sample, second_sample, key=lambda x: x[1])


def watch(detectors, target_field, threshold,
          num=None, trigger_and_read=None, delay=None):
    """Watch a group of detectors and raise if a threshold is breached"""
    trigger_and_read = trigger_and_read or bps.trigger_and_read

    def trigger_and_compare():
        event = yield from trigger_and_read(detectors)
        if event[target_field] < threshold:
            raise SignalLostError("Signal measured at %r, "
                                  "lower than threshold at %r",
                                  sample, threshold)

    return (yield from bps.repeat(trigger_and_compare,
                                  num=max_counts,
                                  delay=None))


def calibrate(detectors, target_field, num, percentile,
              trigger_and_read=None, delay=None):
    """Measure a group of detectors and return percentile of events seen"""
    trigger_and_read = trigger_and_read or bps.trigger_and_read
    events = list()

    @bpp.subs_decorator({'events': [lambda x, y: events.append(y)]})
    def inner_plan():
        # Gather
        yield from bps.repeat(trigger_and_read(detectors,
                                               num=num,
                                               delay=delay))
        # Analyze
        return np.percentile([event[target_field] for event in events],
                             percentile)

    return (yield from inner_plan())


def search(detectors, target_field, motor, *args, num=None, per_step=None):
    """Search a given area via standard scan and return largest event"""
    events = list()
    scan = bpp.stub_wrapper(bp.scan)

    @bpp.subs_decorator({'events': [lambda x, y: events.append(y)]})
    def inner_plan():
        # Gather
        yield from scan(detectors, motor, *args, num=num, per_step=per_step)
        # Analyze
        return sorted(events, key=lambda x: x[target_field])[0]

    return (yield from inner_plan())
