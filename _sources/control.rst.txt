.. _control:

Jet Control Overview
####################

.. currentmodule:: jet_tracking.jet_control

To start IPython for CXI hutch-python3:

.. code-block:: bash

    /reg/g/pcds/pyps/apps/hutch-python/cxi/cxipython

There is a soft link in ``~cxiopr/bin``, so that on CXI machines, one can start
IPython as follows:

.. code-block:: bash

    cxi3


JetControl
==========
Jet tracking control class.

.. autosummary::
    :nosignatures:
    :toctree: generated

    JetControl

Attributes
----------

.. autosummary::
    :toctree: generated/

    JetControl.set_beam
    JetControl.calibrate
    JetControl.jet_calculate
    JetControl.jet_move
