# SiMon -- Simulation Monitor

**SiMon** is an automatic monitor/scheduler/pipeline for astrophysical N-body simulations. In astrophysics, it is common that a grid of simulations is needed to explore a parameter space. SiMon facilitates the paramater-space study simulations in the follow ways:

* Generate an overview of the current simulation status
* Automatically restart the simulation if the code crashes
* Invoke the data processing script (e.g. create plots) once the simulation is finish
* Notify the user (e.g. by email) once the simulations are finished
* Report to the user if a certain simulation cannot be restarted (e.g. code keeps crashing for some reasons)
* Allow the user to define the maximum concurrent instances of simulation, the maximum CPU and GPU usage for each simulation instance
* When the total number of simulations exceeds the capacity of machine concurrency, automatically schedule the next simulation when the current simulation is finished.
* Detect and kill hung simulations (simulations that utilize 100% CPU/GPU but do not make any progress for a long period of time)

Currently, SiMon supports only the NBODY6 direct N-body code. More generic supports to be expected soon.
