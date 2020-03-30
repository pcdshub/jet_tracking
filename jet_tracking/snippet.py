# python code to load and run jet tracking GUI from cxipython

# ipython magic to bootstrap Qt event loop in iPython
%gui qt

import pydm

# 'real' jet tracking GUI
# from jet_tracking.jettracking import JetTrack

# jet tracking GUI for testing
from jet_tracking.testscreen import JetTrack

# load PyDM application
app = pydm.application.PyDMApplication()

# fill widget variable with instance of jet tracking Display class
# pass Ophyd objects as arguments for Display
jt_macros = {'PARAMS': 'CXI:SC1:INLINE', 'REQ': 'CXI:JTRK:REQ', 'PASS': 'CXI:JTRK:PASS'}
widget = JetTrack(JT_input, JT_output, JT_fake, macros=jt_macros)

# load jet tracking GUI
app.main_window.set_display_widget(widget)

# connect PVs -- because PyDM version in cxi3 is too old and does not automatically connect PVs
app.establish_widget_connections(widget)
