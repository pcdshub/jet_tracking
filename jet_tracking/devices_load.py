from hutch_python.utils import safe_load
from .devices import Injector, Questar, Parameters, Offaxis, Diffract, OffaxisParams
from .jet_control import JetControl


"""
Load liquid and Questar camera devices for jet tracking processing
"""

with safe_load('PI1_injector'):
    PI1 = {'name': 'PI1_injector',
           'coarseX': 'CXI:PI1:MMS:01',
           'coarseY': 'CXI:PI1:MMS:02',
           'coarseZ': 'CXI:PI1:MMS:03',
           'fineX': 'CXI:USR:MMS:01',
           'fineY': 'CXI:USR:MMS:02',
           'fineZ': 'CXI:USR:MMS:03'}
    PI1_injector = Injector(**PI1)

with safe_load('SC1_questar'):
    SC1_questar_ports = {'ROI_port': 'ROI1',
                         'ROI_stats_port': 'Stats1',
                         'ROI_image_port': 'IMAGE1'}
    SC1_questar = Questar(**SC1_questar_ports, prefix='CXI:SC1:INLINE',
                          name='SC1_questar')

with safe_load('SC1_params'):
    SC1_params = Parameters(prefix='CXI:SC1:INLINE', name='SC1_params')

with safe_load('SC1_diffract'):
    SC1_diffract = Diffract(prefix='CXI:SC1:DIFFRACT', name='SC1_diffract')

with safe_load('SC1_control'):
    SC1_control = JetControl('SC1_control', PI1_injector, SC1_questar,
                             SC1_params, SC1_diffract)


with safe_load('PI2_injector'):
    PI2 = {'name': 'PI2_injector',
           'coarseX': 'CXI:PI2:MMS:01',
           'coarseY': 'CXI:PI2:MMS:02',
           'coarseZ': 'CXI:PI2:MMS:03',
           'fineX': 'CXI:PI2:MMS:04',
           'fineY': 'CXI:PI2:MMS:05',
           'fineZ': 'CXI:PI2:MMS:06'}
    PI2_injector = Injector(**PI2)

with safe_load('SC2_questar'):
    SC2_questar_ports = {'ROI_port': 'ROI1',
                         'ROI_stats_port': 'Stats1',
                         'ROI_image_port': 'IMAGE1'}
    SC2_questar = Questar(**SC2_questar_ports,
                          prefix='CXI:SC2:INLINE', name='SC2_questar')

with safe_load('SC2_offaxis'):
    SC2_offaxis_ports = {'ROI_port': 'ROI1',
                         'ROI_stats_port': 'Stats1',
                         'ROI_image_port': 'IMAGE1'}
    SC2_offaxis = Offaxis(**SC2_offaxis_ports,
                          prefix='CXI:GIGE:06', name='SC2_offaxis')

with safe_load('SC2_params'):
    SC2_params = Parameters(prefix='CXI:SC2:INLINE', name='SC2_params')

with safe_load('SC2_paroffaxis'):
    SC2_paroffaxis = OffaxisParams(
        prefix='CXI:SC2:OFFAXIS', name='SC2_paroffaxis')

with safe_load('SC2_diffract'):
    SC2_diffract = Diffract(prefix='CXI:SC2:DIFFRACT', name='SC2_diffract')

with safe_load('SC2_control'):
    SC2_control = JetControl('SC2_control',
                             PI2_injector, SC2_questar, SC2_params, SC2_diffract)


with safe_load('PI3_injector'):
    PI3 = {'name': 'PI3_injector',
           'coarseX': 'CXI:PI3:MMS:01',
           'coarseY': 'CXI:PI3:MMS:02',
           'coarseZ': 'CXI:PI3:MMS:03',
           'fineX': 'CXI:PI3:MMS:04',
           'fineY': 'CXI:PI3:MMS:05',
           'fineZ': 'CXI:PI3:MMS:06'}
    PI3_injector = Injector(**PI3)
