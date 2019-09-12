.. _shared_memory:

.. currentmodule:: jet_tracking.psana

Jet Tracking Shared Memory Application
######################################

Information from detectors controled by the LCLS Daq is output to epics PVs through
a psana shared memory application.


SC1 Experiments
---------------

In the standard CXI configuration for the 1 um SC1 chamber,
the following will start a psana shared memomory application for the DSC CsPad detector 
and output information to epics PVs with the base CXI:SC1:DIFFRACT

Normally this application will be run for the primary cxi experiment on daq-cxi-mon01 

.. code-block:: bash 

    /reg/g/pcds/pyps/apps/hutch-python/cxi/cxi/jet_tracking/psana2epics.sh --alias='DscCsPad' --pvbase='CXI:SC1:DIFFRACT'


To check the processing event rate with the daq running, use the caEventRate on
any cxi control room machine

.. code-block:: bash

    caEventRate CXI:SC1:DIFFRACT:TOTAL_ADU.VAL



SC2 Experiments
---------------

For the 100 nm SC2 chamber, the primary daq and daq-cxi-mon01 will generally be used,
and the shared memory application can be started as follows

.. code-block:: bash 

    /reg/g/pcds/pyps/apps/hutch-python/cxi/cxi/jet_tracking/psana2epics.sh --alias='DsaCsPad' --pvbase='CXI:SC2:DIFFRACT'


SC3 Experiments
---------------

For experiments in the SC3 Serial Sample Chamber (a.k.a., SSC chamber), the secondary daq will generally be used,
and the shared memory application will run on daq-cxi-mon06

.. code-block:: bash 

    /reg/g/pcds/pyps/apps/hutch-python/cxi/cxi/jet_tracking/psana2epics.sh --alias='DsdCsPad' --pvbase='CXI:SC3:DIFFRACT'



API
---

.. autosummary::
    :nosignatures:
    :toctree: generated/

    output_cspad_sum
