.. _installation:

Installation
############

For general PCDS software installation see:

https://pcdshub.github.io/installation.html

The current Conda environment can be set with:

.. code-block:: bash

    source /reg/g/pcds/pyps/conda/py36env.sh


Jet tracking code is installed in the working python3 environment for CXI.

.. code-block:: bash

    /reg/g/pcds/pyps/apps/hutch-python/cxi/cxi/jet_tracking


The jet tracking devices for the CXI SC2 chamber are implemented in the
``beamline.py`` file:

.. code-block:: python

    from pcdsdevices.jet import Injector
    from cxi.jet_tracking.devices import (Diffract, JetCamera, InlineParams,
                                          OffaxisParams)
    from cxi.jet_tracking.jet_control import JetControl

    with safe_load('PI2_injector'):
        PI2_injector = Injector(name='PI2_injector', coarseX='CXI:PI2:MMS:01',
                                coarseY='CXI:PI2:MMS:02', coarseZ='CXI:PI2:MMS:03',
                                fineX='CXI:PI2:MMS:04', fineY='CXI:PI2:MMS:05',
                                fineZ='CXI:PI2:MMS:06')

    with safe_load('SC2_inline'):
        SC2_inline = JetCamera('CXI:SC2:INLINE', name='SC2_inline',
                               ROI_port='ROI1', ROI_stats_port='Stats1',
                               ROI_image_port='IMAGE1')

    with safe_load('SC2_offaxis'):
        SC2_offaxis = JetCamera('CXI:GIGE:06', name='SC2_offaxis',
                                ROI_port='ROI1', ROI_stats_port='Stats1',
                                ROI_image_port='IMAGE1')

    with safe_load('SC2_inlineparams'):
        SC2_inlineparams = InlineParams('CXI:SC2:INLINE', name='SC2_inlineparams')

    with safe_load('SC2_offaxisparams'):
        SC2_offaxisparams = OffaxisParams('CXI:SC2:OFFAXIS',
                                          name='SC2_offaxisparams')

    with safe_load('SC2_diffract'):
        SC2_diffract = Diffract('CXI:SC2:DIFFRACT', name='SC2_diffract')

    with safe_load('SC2_control'):
        SC2_control = JetControl('SC2_control', PI2_injector, SC2_inline,
                                 SC2_inlineparams, SC2_diffract)
