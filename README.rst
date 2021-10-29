.. role:: raw-html-m2r(raw)
   :format: html


LCLS Jet Tracking Application
=============================

.. image:: https://img.shields.io/travis/pcdshub/jet_tracking.svg
        :target: https://travis-ci.org/pcdshub/jet_tracking

.. image:: https://img.shields.io/pypi/v/jet_tracking.svg
        :target: https://pypi.python.org/pypi/jet_tracking

The purpose of this application is to automate the positioning of the liquid jet to be conincident with the x-rays.  This version is a start and mostly a proof of concept, because everyone knows you don't build something right the first time ever.  Once this is fully functional then it can be rebuilt with a better architecture and file structure using the proven pieces.

Calibration
-----------

The calibration piece is used to identify the typical diffraction ring intensity from the solvent/substrate present in the liquid jet.  The current procedure is to take about 10 seconds of data in a recorded run then analyze the following:


* Making a cut on the distribution of incoming x ray intensity to identify events with good x ray intensity
* Get the azimuthal average of the area detector for all of those events and identifying the peak intensity (brightest bin of the ring).  Then summing the intensities of the peak bin and a +/- delta bin value.
* Get the projection of the jet camera and identify the peak intensity and location of that jet.

How to run the calibration
^^^^^^^^^^^^^^^^^^^^^^^^^^

There are two ways to run the calibration.\ :raw-html-m2r:`<br>`
The suggested/production way is to run through Automatic Run Processing on pswww.
There is a current definition and run setup for xcsx39718 on Run 82.  You can see the results in the summaries tab for that experiment (elog (aka Data Manager) on pswww)

All of the meta data information is then saved in a json file with the path:
/cds/data/psdm/\ :raw-html-m2r:`<hutch>`\ /\ :raw-html-m2r:`<experiment>`\ /calib/jt_results

The second way to run the calibration is to do it locally, this is much easier for development.  In order to simplify and organize meta data as input parameters for the calibration we use config files located at /jet_tracking/jt_configs.  You need to change information there is you want to adjust certain calibration parameters.  to run you must be on a psana node

.. code-block::

   $ ssh psana
   $ cd <base_path>/jet_tracking/jet_tracking/jet_tracking_cal
   $ source /reg/g/psdm/etc/psconda.sh -py3
   $ python jt_cal.py --cfg <path_to_config_file>  # The default is xcs_config.yml so no arg required if using that one

Sample Output

.. code-block::

   (ana-4.0.20-py3) aegger@psanagpu112:/cds/group/pcds/epics-dev/aegger/jet_tracking/jet_tracking/jet_tracking_cal$ python jt_cal.py
   Will save small data to /reg/d/psdm/xcs/xcsx39718/scratch/run10_jt_cal.h5
   Gathering small data for exp: xcsx39718, run: 10, events: 500
   Detectors Available: [('XcsEndstation.1:ControlsCamera.16', 'xcs_yag4', ''), ('EBeam', '', ''), ('FEEGasDetEnergy', '', ''), ('XCS-IPM-01', '', ''), ('XCS-IPM-03', '', ''), ('XCS-DIO-03', '', ''), ('HX2-SB1-BMMON', '', ''), ('XCS-SB1-BMMON', '', ''), ('XCS-SB2-BMMON', '', ''), ('XcsEndstation.0:Epix10ka.1', 'epix10k135', ''), ('NoDetector.0:Evr.0', 'evr0', ''), ('XcsEndstation.0:Epix10ka2M.0', 'epix10k2M', ''), ('XcsEndstation.1:Opal1000.1', 'opal_1', ''), ('ControlData', '', '')]
   Unable to process event 0: 'NoneType' object has no attribute 'TotalIntensity'
   Saved Small Data, Processing...
   Results: {'i0_low': 53345.170000000006, 'i0_high': 93364.9225, 'i0_median': 74307.8975, 'peak_bin': 12, 'delta_bin': 3, 'mean_ratio': 0.1453248744739173, 'med_ratio': 0.1463255684260074, 'std_ratio': 0.03161866013604559, 'jet_location_mean': 0.0, 'jet_location_std': 0.0, 'jet_peak_mean': 30354.924, 'jet_peak_std': 326.71924}
   Creating Path /reg/d/psdm/xcs/xcsx39718/stats/summary/jt_cal_run_10
   Saving report to /reg/d/psdm/xcs/xcsx39718/stats/summary/jt_cal_run_10/report.html
   finished with jet tracking calibration
   Closing remaining open files:run10_jt_cal.h5...done

Running the shared memory process
---------------------------------

Once we have the needed calibration data, you can run the shared memory process

Sim Mode
^^^^^^^^

If you set the sim variable to true in the config file, you will run in sim mode.  This means you will read offline data.  This is only setup to use one worker and a master so it's somewhat slow, but very good for debugging.

.. code-block::

   $ ssh psana
   $ cd <base_path>/jet_tracking/jet_tracking/mpi_scripts
   $ ./run_mpi_script

Shared Memory
^^^^^^^^^^^^^

To run in shared memory you need to ssh to the mon node that has shared memory running.

.. code-block::

   $ ssh daq-cxi-mon01
   $ cd <base_path>/jet_tracking/jet_tracking/mpi_scripts
   $ ./run_mpi_script -p 8  # -p tells number of cores to use 1 Master, the reset workers
