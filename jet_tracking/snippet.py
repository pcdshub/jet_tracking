# python code to load and run jet tracking GUI from cxipython

import pydm
from IPython import get_ipython

# 'real' jet tracking GUI
# from jet_tracking.jettracking import JetTrack

# jet tracking GUI for testing
from jet_tracking.testscreen import JetTrack

# ipython magic to bootstrap Qt event loop in iPython
get_ipython().run_line_magic('gui', 'qt')

# load PyDM application
app = pydm.application.PyDMApplication()

# This script will not work and I don't think it ever did
# I'm just filling up these values to make flake8 happy
JT_input = "FOO"
JT_output = "BAR"
JT_fake = "BLAH"

# fill widget variable with instance of jet tracking Display class
# pass Ophyd objects as arguments for Display
jt_macros = {'PARAMS': 'CXI:SC1:INLINE', 'REQ': 'CXI:JTRK:REQ', 'PASS': 'CXI:JTRK:PASS'}
widget = JetTrack(JT_input, JT_output, JT_fake, macros=jt_macros)

# load jet tracking GUI
app.main_window.set_display_widget(widget)

# connect PVs -- because PyDM version in cxi3 is too old and does not automatically connect PVs
app.establish_widget_connections(widget)
