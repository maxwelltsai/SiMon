# SiMon -- Simulation Monitor

![alt tag](https://cloud.githubusercontent.com/assets/11092373/25200544/faf80cb2-254e-11e7-915c-c4dea66e2424.png)

**SiMon** is an automatic monitor/scheduler/pipeline for astrophysical N-body simulations. In astrophysics, it is common that a grid of simulations is needed to explore a parameter space. SiMon facilitates the paramater-space study simulations in the follow ways:

* Generate an overview of the current simulation status
* Automatically restart the simulation if the code crashes
* Invoke the data processing script (e.g. create plots) once the simulation is finish
* Notify the user (e.g. by email) once the simulations are finished
* Report to the user if a certain simulation cannot be restarted (e.g. code keeps crashing for some reasons)
* Allow the user to define the maximum concurrent instances of simulation, the maximum CPU and GPU usage for each simulation instance
* When the total number of simulations exceeds the capacity of machine concurrency, automatically schedule the next simulation when the current simulation is finished.
* Detect and kill stalled simulations (simulations that utilize 100% CPU/GPU but do not make any progress for a long period of time)

**SiMon** is highly modular. Arbitrary N-body codes can be supported by **SiMon** by overriding `module_common.py`.

# Installation

**SiMon** depends on `python-daemon`. If you do not have this installed in your Python environment, you could install with

    pip install python-daemon

To install the latest stable version of **SiMon**, you can do

    pip install astro-simon
    
Or you can install the latest developer version from the git repository using:

    pip install https://github.com/maxwelltsai/SiMon/archive/master.zip
    
# Usage

### Generate a grid of demo simulations (Optional)

Navigate to the main code directory of SiMon, and execute the script: 

    python ic_generator_demo.py
    
This will create a grid of pseudo simulations in the directory `examples`.

### Edit the config file

Edit the global SiMon config file `SiMon.conf` accordingly.

### Start/Stop the SiMon Daemon

You could run or stop SiMon as a daemon program for a collection of simulations as:

    python simon.py start|stop    
or

    simon start|stop
    
### Interactive mode
Check simulation status and control the simulations manually:

    python simon.py [interactive]
or

    simon [interactive]
