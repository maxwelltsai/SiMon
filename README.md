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

# Installation

To install the latest stable version of SiMon, you can do

    pip install astro_simon
    
Or you can install the latest developer version from the git repository using:

    pip install https://github.com/maxwelltsai/SiMon/archive/master.zip
    
# Using

### Generate a test simulation file (Optional)

Open `/SiMon/SiMon.conf` and edit the dir from: 

    Root_dir: /Volumes/RamDisk/sim
    
To any directory where can store the test file, eg. `/Users/penny/Works/simon_project/test_code`

Then, change the `sim_root_dir` in icutil_pseudo_simulation.py to dir the same as above.

Generate test file using `python icutil_pseudo_simulation.py`

### Start SiMon

You could run SiMon as a daemon program for a collection of simulations as:

    python simon start
    
Or check simulation status and control by manual through:

    python simon interactive

