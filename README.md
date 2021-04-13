# SiMon -- Simulation Monitor

![alt tag](https://cloud.githubusercontent.com/assets/11092373/25200544/faf80cb2-254e-11e7-915c-c4dea66e2424.png)

**SiMon** is an automatic monitor/scheduler/pipeline for astrophysical N-body simulations. In astrophysics, it is common that a grid of simulations is needed to explore a parameter space. SiMon facilitates the paramater-space study simulations in the follow ways:

* Generate a real-time overview of the current simulation status
* Automatically restart the simulation if the code crashes
* Invoke the data processing script (e.g. create plots) once the simulation is finish
* Notify the user (e.g. by email) once the simulations are finished
* Report to the user if a certain simulation cannot be restarted (e.g. code keeps crashing/stalling for some reasons)
* Parallelize the launching of multiple simulations according to the configured computational resources
* Detect and kill stalled simulations (simulations that utilize 100% CPU/GPU but do not make any progress for a long period of time)

**SiMon** is highly modular. Arbitrary numerical codes can be supported by **SiMon** by overriding `module_common.py` (python programming needed) or editing config files (no programming needed).

**SiMon** is originally built for carrying out large ensembles of astrophysical N-body simulations. However, it has now been generalized to carrying out any computational intensive numerical jobs (e.g., scheduling an observational data reduction pipeline).

# Installation

To install the latest stable version of **SiMon**, you can do

    pip install astrosimon
    
Or you can install the latest developer version from the git repository using:

    pip install https://github.com/maxwelltsai/SiMon/archive/master.zip

Note: as of mid-2019, large number of Python packages have migrated to Python 3.x, with no guarantee of Python 2.x backward compatability. Therefore, **SiMon** is currently optimize for Python 3.x.
    
# Usage - Start with an example code

**SiMon** is simple to use! To display an overview of all managed jobs, you simply type the following in your terminal:

    simon
    
If you would just like to see the currently running jobs, following command will help, the same scheme also applies to check other status such as NEW, DONE, STOP:

    simon | grep RUN
    
If it is your first time running **SiMon**, it will offer to generate a default config file and some demo simulations on the current directly. Just proceed according to the interactive instructions. Then, your simulations can be launched and monitored automatically with
    
    simon start

This will start **SiMon** as a daemon program, which schedule and monitor all simulations automatically without human supervision. The daemon can be stopped with

    simon stop
    
The interactive dashboard of **SiMon** can be launched at any time (before, during, and after the simulations) with this simple command:

    simon -i
    
Or if you prefer: `simon i` or `simon interactive`.
    
# Usage - Apply to your code
Edit the global config file `SiMon.conf` using your favorite text editor, change default

    Root_dir: examples/demo_simulations
    
to be the dir of where your code located, then start simon again!

More detailed configuration can refer https://pennyq.github.io/SiMon/

That's it! Go and take a beer :)


# Paper
http://adsabs.harvard.edu/abs/2017PASP..129i4503Q
