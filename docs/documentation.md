# Documentation for SiMon tool

We will introduce use customizing your simulation integrator and parameter space in this section:

The example case we use here is the [Brutus integrator developed by T. Boekholt and S. Portegies Zwart](https://arxiv.org/pdf/1411.6671.pdf). We will go step by step to show how to apply Brutus integrator into the SiMon tool, so SiMon can auto-iterate parameter space (e.g., number of bodies, word length and tolerance), and restart stopped tasks that are caused by chaotic perturbation.

To generate initiation condition for tasks through parameter space, we can
1. Go to any directories you would prefer, then create a folder for storing initial condition files and/or outputs, in our case, we do
```sh
$ mkdir simon_brutus
$ cd simon_brutus
```
2. Under simon_brutus, run simon and create a config file
```sh
$ simon
Would you like to generate the default SiMon.conf file to the current directory? [Y/N] y
````

3. Copy the initial condition generator template (`ic_generator_demo.py`) from SiMon package to current directory, and rename it
```sh
$ cp ../SiMon/SiMon/ic_generator_demo.py .
$ mv ic_generator_demo.py ic_generator_brutus.py
```

Now under the `simon_brutus` directory, we should have `SiMon.conf` and `ic_generator_brutus.py`, the next step is to modify these two files to match our code.

1. Edit the initial condition generator template (`ic_generator_brutus.py`) with customized settings, in general, the following three parts require user modification

Parameter space: this part is for users to define their parameter space with value array to iterate
```py
tol_exp_vec = [-8, -12, -16, -20, -24]  # tolerance exponent
lw_vec = [72, 88, 104, 120, 136]  # length of word
output_dt_vec = [0.01] # output time step
## initial condition input files
ic_file_list = ['/home/pqian/Brutus_GPU/perturbed_3body.txt', '/home/pqian/Brutus_GPU/unperturbed_3body.txt']
N_vec = [3] # number of objects
t_start = 0 # starting time
t_end = 100 # end time
```
Templates: executable commands for the code to start/restart/stop, etc.

```py
code_name = 'Brutus'
executable_path = os.path.join('/home/pqian/Brutus_GPU', 'brutus') # path of executable brutus code
stop_cmd = '' # edit it only when the code support some ways of gentle stop

# format pattern for the for command to start the simulation, the same for the restart_cmd_template and output_dir_template
start_cmd_template = '%s %d %d %d %d %f %s %s 1>%s 2>%s'
restart_cmd_template = '%s %d %d %d %d %f %s %s 1>%s 2>%s'
output_dir_template = '%s_lw=%d_tol=%d_N=%d'

# generate the initial condition by iterating the parameter space listed in the for loop
# the command string require to be set accordingly to the integrator
for tol_exp in tol_exp_vec:
	for lw in lw_vec:
		for ic_file in ic_file_list:
			for N in N_vec:
				for output_dt in output_dt_vec:
					fmt_str2 = ('%' +('.%df' % abs(tol_exp)))  # to decimal format
					tol_exp_str = str(fmt_str2 % (10**tol_exp))
					start_cmd = start_cmd_template % (executable_path, N, lw, t_start, t_end, output_dt, tol_exp_str, ic_file, 'output.txt', 'error.txt')
					restart_cmd = restart_cmd_template % (executable_path, N, lw, t_start, t_end, output_dt, tol_exp_str, ic_file, 'output.txt', 'error.txt')
					output_dir = output_dir_template % (os.path.basename(ic_file)[:3], lw, abs(tol_exp), N)
					ic.generate_simulation_ic(code_name, t_end, output_dir, start_cmd,
								  input_file='', output_file='output.txt', error_file='error.txt',
								  restart_cmd=restart_cmd, stop_cmd=stop_cmd, niceness=abs(tol_exp)-16)
```


Now we can generate initiation files by running
```sh
$ python ic_generator_brutus.py
```

To check whether the generated initial condition files are correct, you can go into `SiMon.conf`, then copy the `Start_command` and execute directly.

2. Now if you run `simon`, then you will get an empty list of simulation instances. That’s because Simon doesn’t know the new type of integrator/code you have been using. You just need to copy the ```../SiMon/module_demo_simulation.py``` to current directory

Rename the filename:
```sh
$ mv module_demo_simulation.py module_brutus_simulation.py
```

Then edit the `module_brutus_simulation.py` as:
    1. Change `__simulation__ = ‘Brutus’`
    2. Change Class `DemoSimulation` to Class `Brutus`
    3. Change all `super(DemoSimulation, self)…` to `super(Brutus, self)…` (there should be two places to be changed)
    4. Modify the rest of code to extract information from output to your preferred output format, the most important part is to extract the running time and give it to Simon tool, so the SiMon tool can track running time every several seconds (please refer to the `sim_get_model_time(self)` function)
    5. Bonus: run on multiple GPUs (refer to the `sim_start(self)` function)

3. Config the `SiMon.conf according` to the machine condition
```conf
# Global config file for SiMon
[SiMon]

# The simulation data root directory
Root_dir: sim_data

# The time interval for the SiMon daemon to check all the simulations (in seconds) [Default: 180]
Daemon_sleep_time: 120

# The number of simulations to be carried out simultaneously [Default: 2]
Max_concurrent_jobs: 4

# The maximum number of times a simulation will be restarted (a simulation is marked as ERROR when exceeding this limit) [Default: 2]
Max_restarts: 2

# Log level of the daemon: INFO/WARNING/ERROR/CRITICAL [default: INFO]
Log_level: INFO

# The time in second beyond which a simulation is considered stalled
Stall_time: 3600
```

Now you can start running all tasks by running:
```sh
$ simon start
```
And you can always check running status by 
```sh
$ simon
``` 
or interactively control simulations by 
```sh
# simon -i
```


<hr>

What to do when my task is marked as ‘ERROR’?
