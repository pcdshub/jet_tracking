from mpi4py import MPI
import sys
import logging
import numpy as np
import zmq
import time
from epics import caput
from threading import Thread, Lock
from enum import Enum
from collections import deque

f = '%(asctime)s - %(levelname)s - %(filename)s:%(funcName)s - %(message)s'
logging.basicConfig(level=logging.DEBUG, format=f)
logger = logging.getLogger(__name__)


class MpiMaster(object):
    def __init__(self, rank, api_port, det_map, pv_map, sim=True, data_port=8123):
        self._rank = rank
        self._det_map = det_map
        self._pv_map = pv_map
        self._sim = sim
        self._comm = MPI.COMM_WORLD
        self._workers = range(self._comm.Get_size())[1:]
        self._running = False
        self._abort = False
        self._queue = deque()
        self._data_socket = self.get_data_socket()
        self._pub_socket = self.get_pub_socket()
        self._msg_lock = Lock()
        self._msg_thread = Thread(target=self.start_msg_thread, args=(api_port,))
        self._msg_thread.start()
        self.pair_ctx = None
        self.msg_ctx = None

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
            with self._msg_lock:
                self._abort = val

    def get_data_socket(self, data_port=8124):
        """Setup the socket we'll use for client data messaging"""
        if self._sim:
            self.msg_ctx = zmq.Context()
            socket = self.msg_ctx.socket(zmq.PUB)
            socket.bind(''.join(['tcp://*:', str(data_port)]))
            return socket

        return None 

    def get_pub_socket(self, data_port=1235):
        """Socket for publishing API calls to workers"""
        self.msg_ctx = zmq.Context()
        socket = self.msg_ctx.socket(zmq.PUB)
        socket.bind(''.join(['tcp://*:', str(data_port)]))
        return socket

    def start_run(self):
        """Main process loop, we can probably get more async
        but for now it's a one to one recive/send
        """
        while not self.abort:
            start = time.time()
            data = np.empty(len(self._pv_map), dtype=np.dtype(self.det_map['dtype']))
            req = self.comm.Irecv(data, source=MPI.ANY_SOURCE)
            self.send_from_queue()
            req.Wait()
            self.queue.append(data)
            print(time.time() - start)
        self.pair_ctx.close()
        self.msg_ctx.close()
        MPI.Finalize()

    def start_msg_thread(self, api_port):
        """The thread runs a PAIR communication and acts as server side,
        this allows for control of the parameters during data aquisition 
        from some client (probably an API for user). Might do subpub if
        we want messages to be handled by workers as well, or master can
        broadcast information
        """
        self.pair_ctx = zmq.Context()
        socket = self.pair_ctx.socket(zmq.PAIR)
        # TODO: make IP available arg
        socket.bind(''.join(['tcp://*:', str(api_port)]))
        while True:
            message = socket.recv_pyobj()
            print('got message ', message)
            cmd = message['cmd']
            value = message['value']
            if cmd == 'abort':
                self._pub_socket.send_pyobj(message)
                self.abort = True
                logger.info('aborting jet tracking data analysis process')
            elif cmd == 'peak_bin':
                self._pub_socket.send_pyobj(message)
                print('setting peak bin on master')
                msg_string = 'Changing peak bin to {}'.format(value)
                logger.info(msg_string)
            elif cmd == 'delta_bin':
                self._pub_socket.send_pyobj(message)
                print('setting delta bin on master')
                msg_string = 'Changing delta bin to {}'.format(value)
                logger.info(msg_string)
            else:
                print('Received Message with no definition ', message)

    def send_from_queue(self):
        if len(self.queue) > 0:
            data = self.queue.popleft()
            if self._sim:
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
                for k, v in self._pv_map.items():
                    caput(v, data[k])
                #caput('XCS:JTRK:REQ:DIFF_INTENSITY', data[1])
                #caput('XCS:JTRK:REQ:I0', data[0])
        else:
            pass
