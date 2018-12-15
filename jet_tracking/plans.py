import logging
from functools import wraps

import bluesky.preprocessors as bpp
import bluesky.plan_stubs as bps
from .plan_stubs import wiggle, watch, calibrate, search, SignalLostError

logger = logging.getLogger(__name__)


def as_run(func):
    """Create a complete plan from a single function"""
    @wraps(func)
    def with_as_run(self, *args, **kwargs):
        _md = {'plan_name': func.__name__,
               'plan_args': {'per_step': repr(self.per_step),
                             'args': args, 'kwargs': kwargs}}
        _md.update(self.md)
        wrapped_with_run = bpp.run_wrapper(func(self, *args, **kwargs), md=_md)
        wrapped_with_stage = bpp.stage_wrapper(wrapped_with_run,
                                               list(self.detectors)
                                               + [self.motor])
        return (yield from wrapped_with_stage)
    return with_as_run


class JetTracker:

    trigger_and_read = None
    per_step = None

    def __init__(self, detectors, target_field, motor):
        self.detectors = detectors
        self.target_field = target_field
        self.motor = motor

    @property
    def md(self):
        return {'motors': [self.motor.name],
                'detectors': [det.name for det in self.detectors],
                'hints': {'dimensions':  [(self.motor.hints['fields'], 'primary')]},
                'per_step': self.per_step,
                'trigger_and_read': self.trigger_and_read,
                }

    @as_run
    def calibrate(self, percentile, num, delay=None):
        return (yield from calibrate(list(self.detectors) + [self.motor],
                                     self.target_field,
                                     num=num, delay=delay,
                                     percentile=percentile,
                                     trigger_and_read=self.trigger_and_read))

    @as_run
    def wiggle(self, step_size):
        return (yield from wiggle(self.detectors, self.target_field,
                                  self.motor, step_size,
                                  per_step=self.per_step))

    @as_run
    def watch(self, threshold, num=None, delay=None):
        return (yield from watch(list(self.detectors) + [self.motor],
                                 self.target_field,
                                 threshold=threshold,
                                 trigger_and_read=self.trigger_and_read,
                                 num=num, delay=delay))
    @as_run
    def search(self, *args, num):
        return (yield from search(self.detectors, self.target_field, self.motor,
                                  *args, num=num, per_step=self.per_step))

    @as_run
    def wiggle_scan(self, min_wiggle, max_wiggle, dwell=0.1):
        iter_ = 0
        last_intensity = None
        min_wiggle = 0.001
        max_wiggle = 0.003
        step_size = min_wiggle
        while True:
            iter_ += 1
            pos, event = yield from wiggle(self.detectors,
                                               self.target_field,
                                               self.motor,
                                               step_size=step_size,
                                               per_step=self.per_step)

            intensity = event[self.target_field]['value']

            yield from bps.abs_set(self.motor, pos, wait=True)
            logger.info(f'Now at position {pos} with reading {intensity} '
                        f'(step={step_size})')

            if last_intensity is not None:
                step_size = (last_intensity / intensity) * max_wiggle
                step_size = max(min(max_wiggle, step_size), min_wiggle)

            last_intensity = intensity

            yield from bps.sleep(dwell)
