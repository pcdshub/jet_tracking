import psana
from psmon.plots import Image
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from psmon import publish
import numpy as np
import os
import logging
import requests
import socket
import argparse
import sys
import time
import inspect
from mpi4py import MPI

from smalldata_tools.SmallDataUtils import detData

f = '%(asctime)s - %(levelname)s - %(filename)s:%(funcName)s - %(message)s'
logging.basicConfig(level=logging.DEBUG, format=f)
logger = logging.getLogger(__name__)


class MpiWorker(object):
    """This worker will collect events and do whatever
    necessary processing, then send to master"""
    def __init__(self, ds, evnt_lim, detector, ipm, evr, r_mask, latency=0.5, event_code=40, plot=False, peak_bin=25, delta_bin=5):
        self._ds = ds  # We probably need to use kwargs to make this general
        self._evnt_lim = evnt_lim
        self._detector = detector
        self._ipm = ipm
        self._evr = evr
        self._comm = MPI.COMM_WORLD
        self._rank = self._comm.Get_rank()
        self._r_mask = r_mask
        self._plot = plot
        self._latency = latency
        self._event_code = event_code
        self._peak_bin = peak_bin
        self._delta_bin = delta_bin
        self._state = None

    @property
    def rank(self):
        """Worker ID"""
        return self._rank

    @property
    def evnt_lim(self):
        """Number of events for worker to process"""
        return self._evnt_lim

    @property
    def ds(self):
        """DataSource object"""
        return self._ds

    @property
    def detector(self):
        """Detectors to get data from"""
        return self._detector

    @property
    def comm(self):
        """MPI communicator"""
        return self._comm

    @property
    def ipm(self):
        """IPM Detector"""
        return self._ipm

    @property
    def evr(self):
        """EVR detector"""
        return self._evr

    @property
    def plot(self):
        """Whether we should plot detector"""
        return self._plot

    @property
    def latency(self):
        """Max latency allowed between event and results"""
        return self._latency

    @property
    def event_code(self):
        """Event Code to trigger data collection on"""
        return self._event_code

    @property
    def peak_bin(self):
        return self._peak_bin

    @peak_bin.setter
    def peak_bin(self, peak_bin):
        try:
            self._peak_bin = int(peak_bin)
        except:
            logger.warning('You must provide int for peak bin')

    @property
    def delta_bin(self):
        return self._delta_bin

    @delta_bin.setter
    def delta_bin(self, delta_bin):
        try:
            self._delta_bin = int(delta_bin)
        except:
            logger.warning('You must provide int for delta bin')

    def start_run(self):
        """Worker should handle any calculations"""
        #mask_det = det.mask(188, unbond=True, unbondnbrs=True, status=True,  edges=True, central=True)
        ped = self.detector.pedestals(1)[0]
        for evt_idx, evt in enumerate(self.ds.events()):
            if self.event_code not in self.evr.eventCodes(evt):
                 continue
            low_bin = self.peak_bin - self.delta_bin
            hi_bin = self.peak_bin + self.delta_bin
            raw = (self.detector.raw_data(evt) - ped)
            data = self.detector.image(evt, raw)
            az_bins = np.array([np.mean(data[mask]) for mask in self._r_mask[low_bin:hi_bin]])
            intensity = np.sum(az_bins)
            try:
                i0 = self.ipm[0].get(evt)
                if self.ipm[1]:
                    det = getattr(i0, self.ipm[1])
                    i0 = det()
            except:
                i0 = 0.0
            
            packet = np.array([i0, intensity], dtype='float32')
            self.comm.Isend(packet, dest=0, tag=self.rank)
