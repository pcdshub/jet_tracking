import time
from functools import partial
import logging

import bluesky.plan_stubs as bps
import bluesky.preprocessors as bpp
import bluesky.plans as bp
from bluesky.utils import (Msg, short_uid)

import numpy as np
import pandas as pd

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
        return (position, event)

    # Sample all of our points
    start_position = motor.position
    start_sample = yield from sample_at_point(start_position)
    first_sample = yield from sample_at_point(start_position + step_size)
    second_sample = yield from sample_at_point(start_position - step_size)

    value = max(start_sample, first_sample, second_sample,
                key=lambda x: x[1][target_field]['value'])
    logger.info("Found maximum value of %r at %r",
                value[1][target_field]['value'], value[0])
    return value


def watch(detectors, target_field, threshold,
          num=None, trigger_and_read=None, delay=None):
    """Watch a group of detectors and raise if a threshold is breached"""
    trigger_and_read = trigger_and_read or bps.trigger_and_read

    def trigger_and_compare():
        event = yield from trigger_and_read(detectors)
        sample = event[target_field]['value']
        if sample < threshold:
            raise SignalLostError(f"Signal measured at {sample}, "
                                  f"lower than threshold at {threshold}")

    return (yield from bps.repeat(trigger_and_compare,
                                  num=num,
                                  delay=None))


def calibrate(detectors, target_field, num, percentile,
              trigger_and_read=None, delay=None):
    """Measure a group of detectors and return percentile of events seen"""
    trigger_and_read = trigger_and_read or bps.trigger_and_read
    events = list()

    @bpp.subs_decorator({'event': [lambda x, y: events.append(y)]})
    def inner_plan():
        # Gather
        yield from bps.repeat(partial(trigger_and_read, detectors),
                              num=num,
                              delay=delay)
        # Analyze
        value = np.percentile([event['data'][target_field]
                               for event in events],
                              percentile)
        logger.info("%r percentile of %r readings was %r",
                    percentile, num, value)
        return value

    return (yield from inner_plan())


def search(detectors, target_field, motor, *args, num=None, per_step=None):
    """Search a given area via standard scan and return largest event"""
    events = list()

    @bpp.subs_decorator({'event': [lambda x, y: events.append(y)]})
    def inner_plan():
        # Gather
        yield from bpp.stub_wrapper(bp.scan(detectors, motor,
                                            *args, num=num, per_step=per_step))
        # Analyze
        value = max(events, key=lambda x: x['data'][target_field])
        logger.info("Found a maximum value of %r at %r",
                    value['data'][target_field],
                    value['data'][motor.name])
    return (yield from inner_plan())


def averaged_step(average_counts, detectors, motor, step):
    group = short_uid('set')
    yield Msg('checkpoint')
    yield Msg('set', motor, step, group=group)
    yield Msg('wait', None, group=group)

    def strip_timestamp(reading):
        for name, det_reading in list(reading.items()):
            reading[name] = det_reading['value']
        return reading

    def single_reading():
        reading = (yield from bps.trigger_and_read(list(detectors) + [motor]))
        return strip_timestamp(reading)

    readings = []
    for i in range(average_counts):
        readings.append((yield from single_reading()))

    all_readings = pd.DataFrame.from_records(readings)
    return {key: {'value': all_readings[key].mean(),
                  'timestamp': time.time(),
                  }
            for key in all_readings}
