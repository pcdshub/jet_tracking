Simulations
-----------
Using simulated ``ophyd`` signals, the ``jet_tracking`` library contains a
simple simulation of the relationship between the injector, beam energy and the
total intensity of data seen on the detector. Obviously these simulations
depend on a number of preset values which will affect the shape of the
distribution that we are simulating, a full explanation can be seen below.
However, for those looking for a quick start there are two simulations already
instantiated ``simulation`` and ``noiseless_simulation``.

.. autofunction:: jet_tracking.sim.generate_simulation
