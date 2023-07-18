.. _shared_memory:

.. currentmodule:: jet_tracking.psana

Jet Tracking Shared Memory Application
######################################

Information from detectors controlled by the LCLS Daq is output to EPICS PVs through
a psana shared memory application.


SC1 Experiments
---------------

In the standard CXI configuration for the 1 um SC1 chamber,
the following will start a psana shared memory application for the DSC CSPAD
detector and output information to epics PVs with the base
``CXI:SC1:DIFFRACT``.

Normally this application will be run for the primary CXI experiment on
``daq-cxi-mon01`` with:

.. code-block:: bash

    /reg/g/pcds/pyps/apps/hutch-python/cxi/cxi/jet_tracking/psana2epics.sh --alias='DscCsPad' --pvbase='CXI:SC1:DIFFRACT'


To check the processing event rate with the Daq running, use the
``caEventRate`` on any CXI control room machine:

.. code-block:: bash

    caEventRate CXI:SC1:DIFFRACT:TOTAL_ADU.VAL


SC2 Experiments
---------------

For the 100 nm SC2 chamber, the primary Daq and ``daq-cxi-mon01`` will
generally be used, and the shared memory application can be started as follows:

.. code-block:: bash

    /reg/g/pcds/pyps/apps/hutch-python/cxi/cxi/jet_tracking/psana2epics.sh --alias='DsaCsPad' --pvbase='CXI:SC2:DIFFRACT'


SC3 Experiments
---------------

For experiments in the SC3 Serial Sample Chamber (a.k.a., SSC chamber), the
secondary Daq will generally be used, and the shared memory application will
run on ``daq-cxi-mon06``.

.. code-block:: bash

    /reg/g/pcds/pyps/apps/hutch-python/cxi/cxi/jet_tracking/psana2epics.sh --alias='DsdCsPad' --pvbase='CXI:SC3:DIFFRACT'


API
---
