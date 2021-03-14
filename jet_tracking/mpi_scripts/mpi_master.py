from mpi4py import MPI
import sys
import logging
import numpy as np
import zmq
import time
from epics import caput
from threading import Thread
from enum import Enum
from collections import deque

f = '%(asctime)s - %(levelname)s - %(filename)s:%(funcName)s - %(message)s'
logging.basicConfig(level=logging.DEBUG, format=f)
logger = logging.getLogger(__name__)


class MpiMaster(object):
    def __init__(self, rank, api_port, det_map, pv_map, psana=False, data_port=8123):
        self._rank = rank
        self._det_map = det_map
        self._pv_map = pv_map
        self._psana = psana
        self._comm = MPI.COMM_WORLD
        self._workers = range(self._comm.Get_size())[1:]
        self._running = False
        self._abort = False
        self._queue = deque()
        self._data_socket = self.get_data_socket()
        self._msg_thread = Thread(target=self.start_msg_thread, args=(api_port,))
        self._msg_thread.start()

    @property
    def rank(self):
        """Master rank (should be 0)"""
        return self._rank

    @property
    def comm(self):
        """Master communicator"""
        return self._comm

    @property
    def workers(self):
        """Workers currently sending"""
        return self._workers

    @property
    def det_map(self):
        """Detector info"""
        return self._det_map

    @property
    def queue(self):
        """Queue for processing data from workers"""
        return self._queue

    @property
    def running(self):
        """Check if master is running"""
        return self._running

    @property
    def abort(self):
        """See if abort has been called"""
        return self._abort

    @abort.setter
    def abort(self, val):
        """Set the abort flag"""
        if isinstance(val, bool):
            self._abort = val

    def get_data_socket(self, data_port=8123):
        """Setup the socket we'll use for client data messaging"""
        if self._psana:
            context = zmq.Context()
            socket = context.socket(zmq.PUB)
            socket.bind(''.join(['tcp://*:', str(data_port)]))
            return socket

        return None 

    def start_run(self):
        """Main process loop, we can probably get more async
        but for now it's a one to one recive/send
        """
        while not self.abort:
            start = time.time()
            # TODO: Generalize data length
            data = np.empty(2, dtype=np.dtype(self.det_map['dtype']))
            req = self.comm.Irecv(data, source=MPI.ANY_SOURCE)
            self.send_from_queue()
            req.Wait()
            self.queue.append(data)
            print(time.time() - start)
        MPI.Finalize()

# status = MPI.Status()
# ready = self.comm.Iprobe(source=MPI.ANY_SOURCE, tag=MPI.ANY_TAG, status=status)
# if ready:
# data = np.empty(2, dtype=np.dtype(self.det_map['dtype']))
# self.comm.Recv(data, source=status.Get_source(), tag=MPI.ANY_TAG, status=status)

    def start_msg_thread(self, api_port):
        """The thread runs a PAIR communication and acts as server side,
        this allows for control of the parameters during data aquisition 
        from some client (probably an API for user). Might do subpub if
        we want messages to be handled by workers as well, or master can
        broadcast information
        """
        context = zmq.Context()
        socket = context.socket(zmq.PAIR)
        # TODO: make IP available arg
        socket.bind(''.join(['tcp://*:', str(api_port)]))
        while True:
            message = socket.recv()
            if message == 'abort':
                self.abort = True
                socket.send('aborted')
            else:
                print('Received Message with no definition ', message)

    def send_from_queue(self):
        if len(self.queue) > 0:
            data = self.queue.popleft()
            if self._psana:
                # Could need this if sending large arrays,
                # Could end up getting md info from config file
                md = dict(
                    dtype = str(data.dtype),
                    shape = data.shape
                )
                self._data_socket.send_json(md, 0|zmq.NOBLOCK)
                self._data_socket.send(data, 0, copy=False, track=False)
            else:
                # consider caput_many with lots, ok for now
                #print('caputing data ', data)
                #for k, v in self._pv_map:
                #caput(v, data[k])
                #ratio = data[1] / data[0]
                caput('XCS:JTRK:REQ:DIFF_INTENSITY', data[1])
                caput('XCS:JTRK:REQ:I0', data[0])
                #caput('CXI:JTRK:REQ:RATIO', ratio)
        else:
            pass
