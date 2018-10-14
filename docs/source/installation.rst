.. _installation:

Installation
############

For general pcds software installation see:

https://pcdshub.github.io/installation.html

The current conda environment can be set with:

.. code-block:: bash 

    source /reg/g/pcds/pyps/conda/py36env.sh


Jet tracking code is installed in the working python3 environment for cxi.

.. code-block:: bash 

    /reg/g/pcds/pyps/apps/hutch-python/cxi/cxi/jet_tracking


The jet tracking devices for the cxi SC2 chamber are implemented in the beamline.py file

.. code-block:: python

    from cxi.jet_tracking.devices import Injector, Diffract
    from cxi.jet_tracking.devices import Questar, Parameters
    from cxi.jet_tracking.devices import Offaxis, OffaxisParams
    from cxi.jet_tracking.jet_control import JetControl

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
        SC2_questar = Questar(**SC2_questar_ports, prefix='CXI:SC2:INLINE', name='SC2_questar')

    with safe_load('SC2_offaxis'):
        SC2_offaxis_ports = {'ROI_port': 'ROI1',
                             'ROI_stats_port': 'Stats1',
                             'ROI_image_port': 'IMAGE1'}
        SC2_offaxis = Offaxis(**SC2_offaxis_ports, prefix='CXI:GIGE:06', name='SC2_offaxis')

    with safe_load('SC2_params'):
        SC2_params = Parameters(prefix='CXI:SC2:INLINE', name='SC2_params')

    with safe_load('SC2_paroffaxis'):
        SC2_paroffaxis = OffaxisParams(prefix='CXI:SC2:OFFAXIS', name='SC2_paroffaxis')

    with safe_load('SC2_diffract'):
        SC2_diffract = Diffract(prefix='CXI:SC2:DIFFRACT', name='SC2_diffract')

    with safe_load('SC2_control'):
        SC2_control = JetControl('SC2_control',
                PI2_injector, SC2_questar, SC2_params, SC2_diffract)


     


