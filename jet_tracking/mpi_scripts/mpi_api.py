import yaml
import zmq
import numpy as np
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--cfg_file', help='if specified, has information about what metadata to use', type=str, default='default_config.yml')
args = parser.parse_args()

with open(''.join(['mpi_configs/', args.cfg_file])) as f:
    yml_dict = yaml.load(f, Loader=yaml.FullLoader)
    api_port = yml_dict['api_msg']['port']

context = zmq.Context()
socket = context.socket(zmq.PAIR)
socket.connect(''.join(['tcp://localhost:', str(api_port)]))

# Example for subscribing to np arrays zmq
#context_data = zmq.Context()
#socket_data = context_data.socket(zmq.SUB)
#socket_data.connect(''.join(['tcp://localhost:', '8123']))
#socket_data.subscribe("")  # All topics
#while True:
#    md = socket_data.recv_json(flags=0)
#    msg = socket.recv(flags=0, copy=False, track=False)
#    buf = memoryview(msg)
#    data = np.frombuffer(buf, dtype=md['dtype'])
#    print('data ', data.reshape(md['shape'])) 

def abort():
    """Abort MPI run"""
    socket.send('abort')

def pause():
    """Pause MPI run"""
    socket.send('pause')
