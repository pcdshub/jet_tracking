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
from threading import Thread, Lock
import zmq
from mpi4py import MPI

f = '%(asctime)s - %(levelname)s - %(filename)s:%(funcName)s - %(message)s'
logging.basicConfig(level=logging.DEBUG, format=f)
logger = logging.getLogger(__name__)


class MpiWorker(object):
    """This worker will collect events and do whatever
    necessary processing, then send to master"""
    def __init__(self, ds, detector, ipm, jet_cam, jet_cam_axis, evr, r_mask, calib_results,
                 event_code=40, 
                 plot=False, 
                 data_port=1235):
        self._ds = ds  # We probably need to use kwargs to make this general
        self._detector = detector
        self._ipm = ipm
        self._jet_cam = jet_cam
        self._jet_cam_axis = jet_cam_axis
        self._evr = evr
        self._comm = MPI.COMM_WORLD
        self._rank = self._comm.Get_rank()
        self._r_mask = r_mask
        self._plot = plot
        self._event_code = event_code
        self._peak_bin = int(calib_results['peak_bin'])
        self._delta_bin = int(calib_results['delta_bin'])
        self._i0_thresh = [float(calib_results['i0_low']), float(calib_results['i0_high'])]
        self._state = None
        self._msg_thread = Thread(target=self.start_msg_thread, args=(data_port,))
        self._msg_thread.start()
        self._attr_lock = Lock()
        
        print('I0 threshold: {}, {}'.format(self._i0_thresh[0], self._i0_thresh[1]))

    @property
    def rank(self):
        """Worker ID"""
        return self._rank

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
    def event_code(self):
        """Event Code to trigger data collection on"""
        return self._event_code

    @property
    def peak_bin(self):
        return self._peak_bin

    @peak_bin.setter
    def peak_bin(self, peak_bin):
        with self._attr_lock:
            try:
                self._peak_bin = int(peak_bin)
            except:
                logger.warning('You must provide int for peak bin')

    @property
    def delta_bin(self):
        return self._delta_bin

    @delta_bin.setter
    def delta_bin(self, delta_bin):
        with self._attr_lock:
            try:
                self._delta_bin = int(delta_bin)
            except:
                logger.warning('You must provide int for delta bin')

    @property
    def jet_cam(self):
        return self._jet_cam

    @property
    def jet_cam_axis(self):
        return self._jet_cam_axis

    def start_run(self):
        """Worker should handle any calculations"""
        run = next(self._ds.runs()).run()
        psana_mask = self.detector.mask(int(run), calib=True, status=True, edges=True, central=False, unbond=False, unbondnbrs=False)
        for evt_idx, evt in enumerate(self.ds.events()):
            # Definitely not a fan of wrapping the world in a try/except
            # but too many possible failure modes from the data
            try:
                if self.event_code not in self.evr.eventCodes(evt):
                    continue
                with self._attr_lock:
                    low_bin = self.peak_bin - self.delta_bin
                    hi_bin = self.peak_bin + self.delta_bin
                
                # Get i0 data, this is different for different ipm detectors
                i0 = getattr(self.ipm[0].get(evt), self.ipm[1])()
                # Filter based on i0
                if i0<self._i0_thresh[0] or i0>self._i0_thresh[1]:
                    print('Bad shot')
                    print(i0)
                    dropped = 1
                    intensity = 0
                    inorm = 0
                else:
                    print(i0)
                    dropped = 0

                    # Detector images
                    calib = self.detector.calib(evt)
                    calib = calib*psana_mask
                    det_image = self.detector.image(evt, calib)
                    az_bins = np.array([np.mean(det_image[mask]) for mask in self._r_mask[low_bin:hi_bin]])
                    intensity = np.sum(az_bins)
                    # Normalized intensity
                    inorm = intensity/i0

                    # Get jet projection peak and location
                    if self.jet_cam is not None:
                        jet_proj = self.jet_cam.image(evt).sum(axis=self.jet_cam_axis)
                        max_jet_val = np.amax(jet_proj)
                        max_jet_idx = np.where(jet_proj==max_jet_val)[0][0]
                    else:
                        max_jet_val = None
                        max_jet_idx = None

#                packet = np.array([i0, intensity, inorm, max_jet_val, max_jet_idx], dtype='float32')
                packet = np.array([intensity, i0, inorm, dropped], dtype='float32')
                self.comm.Isend(packet, dest=0, tag=self.rank)
            except Exception as e:
            #else:
                logger.warning('Unable to Process Event: {}'.format(e))
                continue

    def start_msg_thread(self, data_port=1235):
        """The thread runs a PAIR communication and acts as server side,
        this allows for control of the parameters during data aquisition 
        from some client (probably an API for user). Might do subpub if
        we want messages to be handled by workers as well, or master can
        broadcast information
        """
        context = zmq.Context()
        socket = context.socket(zmq.SUB)
        # TODO: make IP available arg
        socket.connect(''.join(['tcp://localhost:', str(data_port)]))
        socket.subscribe('')
        print('running worker message thread')
        while True:
            message = socket.recv_pyobj()
            cmd = message['cmd']
            value = message['value']
            if cmd == 'abort':
                self.abort = True
                logger.info('aborting jet tracking data analysis process')
            elif cmd == 'peak_bin':
                msg_string = 'Worker {} changing peak bin to {}'.format(self.rank, value)
                logger.info(msg_string)
                self.peak_bin = int(value)
            elif cmd == 'delta_bin':
                msg_string = 'Worker {} changing delta bin to {}'.format(self.rank, value)
                logger.info(msg_string)
                self.delta_bin = int(value)
            else:
                logger.warning('Worker {} received message with no definition {}'.format(self.rank, message))

