import os
import os.path
import glob
from fnmatch import fnmatch
import time
import sys
import shutil
import re
import numpy as np
import signal
from simulation_task import SimulationTask


# TODO: move the configuration to a text file called 'SiMon.conf'. Parse the config file with regex.
sim_dir = '/Users/penny/Works/simon_project/nbody6/Ncode/run'  # Global configurations


class SiMon(object):
    """
    Main code of Simulation Monitor (SiMon).
    """
    def __init__(self, pidfile=None, stdin='/dev/tty', stdout='/dev/tty', stderr='/dev/tty',
                 mode='interactive', cwd=sim_dir):
        """
        :param pidfile:
        """
        self.selected_inst = None
        self.id_dict = None
        self.id_dict_short = None
        self.sim_inst_dict = None
        self.sim_inst_parent_dict = None
        self.sim_tree = SimulationTask(0, 'root', cwd, 'STOP')
        self.status_dict = None
        self.stdin_path = stdin
        self.stdout_path = stdout
        self.stderr_path = stderr
        self.pidfile_path = pidfile
        self.pidfile_timeout = 5
        self.mode = mode
        self.cwd = cwd
        self.inst_id = 0
        self.tcrit = 100
        os.chdir(cwd)

    # TODO: how this function get called?
    def id_input(self, prompt):
        """
        Prompt to the user to input the simulation ID.
        """
        confirmed = False
        while confirmed == False:
            ids = raw_input(prompt).split(',')
            if raw_input('Your input is \n\t'+str(ids)+', confirm? [Y/N] ').lower() == 'y':
                confirmed = True
                return ids

    # TODO: more comments
    def traverse_dir2(self, pattern, dir, files):
        """
        Traverse the simulation file structure tree, until the leaf (i.e. no restart directory) or
        the simulation is not restartable (directory with the 'STOP' file).
        """
        for filename in sorted(files):
            if fnmatch(filename, pattern):
                if os.path.isdir(os.path.join(dir, filename)):
                    fullpath = os.path.join(dir, filename)
                    self.inst_id += 1
                    id = self.inst_id
                    self.id_dict[id] = fullpath
                    self.id_dict_short[id] = filename
                    sim_inst = SimulationTask(id, filename, fullpath, 'STOP')
                    self.sim_inst_dict[id] = sim_inst
                    # register child to the parent
                    self.sim_inst_parent_dict[dir].restarts.append(sim_inst)
                    sim_inst.level = self.sim_inst_parent_dict[dir].level + 1
                    # register the node itself in the parent tree
                    self.sim_inst_parent_dict[fullpath] = sim_inst
                    sim_inst.parent_id = self.sim_inst_parent_dict[dir].id

                    # Get simulation status
                    print fullpath
                    try:
                        sim_inst.mtime = os.stat(os.path.join(fullpath, 'output.log')).st_mtime
                        sim_inst.t_min, sim_inst.t_max = self.get_sim_status(fullpath)
                        if sim_inst.t_max > sim_inst.t_max_extended:
                            sim_inst.t_max_extended = sim_inst.t_max
                    except OSError:
                        mtime = 'NaN'
                        sim_inst.t_min = 0
                        sim_inst.t_max = 0
                    try:
                        sim_inst.ctime = os.stat(os.path.join(fullpath, 'start_time')).st_ctime
                    except OSError:
                        ctime = 'NaN'
                    try:
                        if os.path.isfile(os.path.join(fullpath, 'process.pid')):
                            fpid = open(os.path.join(fullpath, 'process.pid'),'r')
                            pid = 0
                            pid = int(fpid.readline())
                            try:
                                if pid > 0:
                                    os.kill(pid, 0)
                                    sim_inst.status = 'RUN [%d]' % (pid)
                            except (ValueError, OSError, Exception), e:
                                sim_inst.status = 'STOP'
                            fpid.close()
                        else: # process not running or pid file not exist
                            if time.time()-sim_inst.mtime<120: sim_inst.status = 'RUN'
                            else: sim_inst.status = 'STOP'
                        if self.check_instance_hanged(id) == True:
                            sim_inst.status += ' HANG'
                        if self.tcrit - sim_inst.t_max < 100:
                            sim_inst.status = 'DONE'
                    except Exception:
                        sim_inst.status = 'NaN'
                    self.status_dict[id] = sim_inst.status
                    sim_inst.errortype = self.check_instance_error_type(id)
                    self.sim_inst_parent_dict[dir].status = sim_inst.status
                    self.status_dict[self.sim_inst_parent_dict[dir].id] = sim_inst.status
                    #if sim_inst.t_max_extended > self.sim_inst_parent_dict[dir].t_max_extended+50 and not os.path.isfile(os.path.join(sim_inst.fulldir,'NORESTART')):
                    if sim_inst.t_max_extended > self.sim_inst_parent_dict[dir].t_max_extended and not os.path.isfile(os.path.join(sim_inst.fulldir,'NORESTART')):
                        # nominate as restart candidate
                        self.sim_inst_parent_dict[dir].cid = sim_inst.id
                        self.sim_inst_parent_dict[dir].t_max_extended = sim_inst.t_max_extended

    def gen_instance_list(self):
        """
        Generate the simulation tree data structure, so that a restarted simulation can trace back
        to its ancestor.

        :return: The method has no return. The output of the method is on the TTY.
        :type: None
        """
        os.chdir(self.cwd)
        self.id_dict = dict()
        self.id_dict_short = dict()
        self.sim_inst_dict = dict()
        self.sim_inst_parent_dict = dict()
        self.status_dict = dict()
        self.sim_tree = SimulationTask(0, 'root', self.cwd, 'STOP')
        self.sim_inst_dict[0] = self.sim_tree
        self.sim_inst_parent_dict[self.cwd.strip()] = self.sim_tree
        #id_list, id_list_short = self.traverse_dir()
        self.inst_id = 0
        self.status_dict = dict()
        os.path.walk(self.cwd, self.traverse_dir2, '*')
        # Synchronize the status tree
        update_needed = True
        iter = 0
        while update_needed and iter<30:
            iter += 1
            inst_status_modified = False
            for i in self.sim_inst_dict:
                if i == 0:
                    continue
                inst = self.sim_inst_dict[i]
                if 'RUN' in inst.status or 'DONE' in inst.status:
                    if inst.parent_id>0 and self.sim_inst_dict[inst.parent_id].status != inst.status:
                        self.sim_inst_dict[inst.parent_id].status = inst.status
                        inst_status_modified = True
            if inst_status_modified == True:
                update_needed = True
            else:
                update_needed = False
        print self.sim_tree

    def get_sim_status(self, sim_dir):
        """
        Output an overview of the simulation status in the terminal.

        :param sim_dir: simulation running dir
        :type sim_dir: basestring

        :return: start and stop time
        :rtype: int
        """
        t_list = []
        try:
            # TODO: remove mtime?
            mtime = os.stat(os.path.join(sim_dir, 'output.log')).st_mtime
            flog = open(os.path.join(sim_dir, 'output.log'))
            regex = re.compile('^ T = +([^,]\d+)')
            line = flog.readline()
            while line != '':
                res = regex.findall(line)
                if len(res) > 0:
                    t_list.append(int(res[0]))
                line = flog.readline()
            flog.close()
        except OSError:
            mtime = 'NaN'
        if len(t_list) > 0:
            return np.min(t_list), np.max(t_list)
        else:
            return 0, 0

    def check_instance_hanged(self, inst_id):
        """
        Check if a simulation is hung.

        Sometimes, due to numerical difficulties (e.g. numerical singularity), the code
        becomes so slow that it does not make any progress for a long period of time.
        In such case, it is important to identify this behavior, kill the code, modify the
        time step parameters accordingly and then restart the code.
        """
        hanged = False
        inst_dir = self.id_dict[inst_id]
        if os.path.isfile(os.path.join(inst_dir, 'process.pid')):
            try:
                fpid = open(os.path.join(inst_dir, 'process.pid'), 'r')
                try:
                    pid = 0
                    pid = int(fpid.readline())
                except ValueError:
                    sys.stdout.write('Error reading pid file for instance %d\n' % inst_id)
                fpid.close()
                if pid > 0:
                    os.kill(pid, 0)  # test if process exist

                # Exist, then test the file activity
                if os.path.isfile(os.path.join(inst_dir, 'output.log')):
                    mtime = os.stat(os.path.join(inst_dir, 'output.log')).st_mtime
                    if time.time()-mtime<7200:
                        hanged = False
                    else:
                        hanged = True
                else:  # log file not exist, cannot determine whether or not hanged
                    hanged = False
            except OSError, err:  # process may not exist, then instance not running
                err = str(err)
                if err.find("No such process") > 0:
                    hanged = False
        else:  # pid not exist, cannot determine whether the instance is running or not
            hanged = False

        return hanged

    def check_instance_error_type(self, inst_id):
        """
        Check the error type of an NBODY6 simulation from the tail of NBODY6 output.

        :return: return error type
        :type: string
        """
        errortype = ''
        inst_dir = self.id_dict[inst_id]

        # check output log for error type info
        if os.path.isfile(os.path.join(inst_dir, 'output.log')):
            flog = open(os.path.join(inst_dir, 'output.log'), 'r')
            line = flog.readline()
            regex_small_step = re.compile('SMALL STEP')
            regex_halt = re.compile('CALCULATIONS HALTED')
            while line != '':
                res = regex_small_step.findall(line)
                if len(res)>0:
                    errortype = 'SMALL STEP'
                    break
                else:
                    res = regex_halt.findall(line)
                    if len(res)>0:
                        errortype = 'CALCULATIONS HALTED'
                        break
                line = flog.readline()
            flog.close()

            # if cannot find anything from output.log, try to find from output.err (output the last line)
            if errortype == '':
                ferr = open(os.path.join(inst_dir, 'output.err'), 'r')
                line = ferr.readline()
                last_line = line
                while line != '':
                    line = ferr.readline()
                    if line!='':
                        lastline = line
                ferr.close()
                try:
                    errortype = lastline.strip()
                except UnboundLocalError:
                    errortype = 'unknown'
        else:
            errortype = 'unknown'

        return errortype

    def inst_start_new(self):
        """Start a new Nbody6 simulation,
        """
        for s in self.selected_inst:
            s = int(s)
            sys.stdout.write("Starting #%d ==> %s\n" % (s, self.id_dict[s]))
            # for each instance processing, there is a process.pid file, which contains a number
            # later process.pid will be overwrote or created by run.sh - os.system('sh run.sh')
            #
            # late line on run.sh:
            # ../../nbody6 < input 1>output.log 2>output.err  & echo $! > process.pid
            if os.path.isfile(os.path.join(self.id_dict[s], 'process.pid')):
                try:
                    fpid = open(os.path.join(self.id_dict[s], 'process.pid'), 'r')
                    pid = int(fpid.readline())
                    fpid.close()
                    if pid > 0:
                        os.kill(pid, 0)  # test if process exist, if not then an OSError will pop up
                        sys.stdout.write('WARNING: the instance is already running. Will not start new run.\n')
                        return
                except (ValueError, OSError):  # the instance is not running, can start a new instance
                    os.chdir(self.id_dict[s])
                    # scan and remove any previous restarting dirs

                    # a restart dir is created for restoring new restart result, without overwirte previous ones
                    # coz the restart will start from the crashed point eg.[T=20]
                    restart_dir = glob.glob('restart*/')
                    for r_dir in restart_dir:
                        shutil.rmtree(r_dir)
                    os.system('sh run.sh')
                    os.chdir('..')
            else:
                os.chdir(self.id_dict[s])
                # scan and remove any previous restarting dirs
                restart_dir = glob.glob('restart*/')
                for r_dir in restart_dir:
                    shutil.rmtree(r_dir)
                os.system('sh run.sh')
                os.chdir('..')
        # reset the selected instance
        self.selected_inst = None

    def inst_restart(self):
        """
        Restart an NBODY6 Simulation.
        """
        # restart.sh content
        restart_script_template = """touch 'start_time'
        export OMP_NUM_THREADS=2
        export GPU_LIST="%d"
        rm fort.* OUT* ESC COLL COAL data.h5part
        ../../nbody6 < input 1>output.log 2>output.err &
        echo $! > process.pid
        """

        for r in self.selected_inst:
            r = int(r)  # ID of the instance
            sys.stdout.write("Restarting #%d ==> %s\n" % (r, self.id_dict[r]))

            # Retrieve a list of restart files
            original_dir = os.getcwd()
            os.chdir(self.id_dict[r])
            rfiles = glob.glob('restart.tmp.*')  # * here stands for time
            os.chdir(original_dir)

            try:
                # last time of backing up the restart file
                rfile_list = sorted(rfiles, key=lambda fn: int(fn.split('.')[2]))
            except ValueError, e:
                print e
                rfile_list = sorted(rfiles)

            # Retrieve a list of restart directories
            rdir_list = glob.glob(os.path.join(self.id_dict[r], 'restart*/'))

            '''
            nbody will generate some restart.tmp, overwrote every 2 min
            so SiMon need to backup each restart.tmp with time

            every time SiMon will check former T-period restart.tmp (the back up one)
            to try to restart from current T-period, in a iterated way
            While when Simon runs out of all tmp resources, a No-Restart file will be created
            and this instance is gave up and never restarted :(

            TODO: find a theory for this idea!
            '''

            # len(rdir_list) : how many times it gets crashed
            # len(rfile_list) : how many restart tmp files -> running time
            if len(rfile_list) > len(rdir_list):
                restart_dir_name = 'restart'+str(len(rdir_list)+1)
                restart_file_name = os.path.join(self.id_dict[r], rfile_list[len(rfile_list)-1-len(rdir_list)])
                sys.stdout.write('The file %s will be used for restart.\n' % restart_file_name)
            else:
                sys.stderr.write('ERROR [SEVERE]: unable to proceed the simulation %s\n' % self.id_dict[r])
                fnorestart = open(os.path.join(self.id_dict[r], 'NORESTART'), 'w')
                fnorestart.write('NORESTART')
                fnorestart.close()
                return

            # check error type to restart accordingly
            errortype = self.check_instance_error_type(r)
            os.chdir(self.id_dict[r])
            os.mkdir(restart_dir_name)  # restart 1 , 2, 3 ...

            # restart.dat: latest of restart.tmp in nbody code
            if os.path.isfile(restart_file_name):
                shutil.copyfile(restart_file_name, os.path.join(restart_dir_name, 'restart.dat'))
            else:
                shutil.copyfile('restart.tmp', os.path.join(restart_dir_name, 'restart.dat'))
            sys.stdout.write('\t\t%s ==> %s/restart.dat\n' % (restart_file_name, restart_dir_name))

            if os.path.isfile('restart.sh'):
                shutil.copyfile('restart.sh', os.path.join(restart_dir_name, 'run.sh'))
            else:
                f_restart = open(os.path.join(restart_dir_name, 'run.sh'), 'w')
                d_name = self.id_dict[r]
                # TODO: ignore pot_type
                pot_type = ''
                if 'pm' in d_name:
                    pot_type = 'pm'
                elif 'iso' in d_name:
                    pot_type = 'iso'
                elif 'power' in d_name:
                    pot_type = 'power'
                f_restart.write(restart_script_template % (r%4, '../'*(self.sim_inst_dict[r].level+1), pot_type))
                f_restart.close()

            # create input file for restart
            input_file = open(os.path.join(restart_dir_name, 'input'), 'w')
            sys.stdout.write('Instance error type: ' + errortype + '\n')

            # create a new restart input file according to error type
            restart_file_text = self.smart_restart(errortype)
            sys.stdout.write(restart_file_text+'\n')
            input_file.write(restart_file_text)
            input_file.close()

            os.chdir(restart_dir_name)
            os.system('sh run.sh')
            os.chdir('../..')

        # reset the selected instance
        self.selected_inst = None

    def smart_restart(self, errortype):
        """
        Rewrite input file with error type relevant text.
        """
        if errortype == 'SMALL STEP':
            restart_file_text = '4 10000000.0\n0.03 0.02 0.02 0.0 0.0 0\n30000 0 0\n30000 0 0'
        elif errortype == 'CALCULATIONS HALTED':
            restart_file_text = '4 10000000.0\n0.01 0.01 0.01 0.0 0.0 0\n30000 0 0\n30000 0 0'
        else:
            restart_file_text = '4 10000000.0\n0.02 0.02 0.02 0.0 0.0 0\n30000 0 0\n30000 0 0'
        return restart_file_text

    def inst_kill(self):
        """
        Kill the UNIX process of a simulation.
        """
        for k in self.selected_inst:
            k = int(k)
            inst_dir = self.id_dict[k]
            if os.path.isfile(os.path.join(inst_dir, 'process.pid')):
                fpid = open(os.path.join(inst_dir, 'process.pid'), 'r')
                try:
                    pid = 0
                    pid = int(fpid.readline())
                except (ValueError, OSError), e:
                    sys.stdout.write('Unable to kill instance #%d: unable to determine pid.\n' % k)
                fpid.close()
                if self.mode == 'interactive':
                    confirm = raw_input('Are you sure you would like to kill the instance #%d? [Y/N] '
                                        % k).lower()
                else:
                    try:
                        if pid > 0:
                            os.kill(pid, signal.SIGKILL)
                            sys.stdout.write('Instance %d [pid=%d] killed.\n' % (k, pid))
                    except OSError, err:
                        sys.stdout.write('Cannot kill the process: \n' + str(err))
            else:  # TODO: here the else should be 'no process.pid file found'
                sys.stdout.write('Unable to kill instance #%d: unable to determine pid.\n' % k)

        # reset the selected instance
        self.selected_inst = None

    def inst_backup(self):
        """
        Backup the simulation data files and restart files.

        Notes
        -------
        Sometimes, a code crashes during the output of its data file, corrupting the output/restart file.
        The consequence of this corruption is fatal, because this makes it impossible to read the data even
        after the simulation finishes, and/or making it impossibe to restart the simulation when it crashes.

        SiMon peroidically backs up those important files.
        """
        # TODO: more comments here?
        for i in self.selected_inst:
            i = int(i)
            inst_dir = self.id_dict[i]  # code input dir

            # min and max T
            t_min, t_max = self.get_sim_status(inst_dir)
            original_dir = os.getcwd()
            os.chdir(inst_dir)
            restart_file_list = glob.glob('restart.tmp.*')
            need_backup = True

            for rf in restart_file_list:  # string of restart file name
                if str(t_max) in rf:
                    # if the simulation process doesn't make progress since last back up
                    # then the backup file is already the latest one, no need to back up
                    need_backup = False
                    break

            if need_backup:
                restart_file_name = 'restart.tmp.'+str(t_max)
                if os.path.isfile('restart.tmp'):
                    shutil.copyfile('restart.tmp', restart_file_name)
                elif os.path.isfile('restart.prev'):
                    shutil.copyfile('restart.prev', restart_file_name)
                sys.stdout.write('Restart file has been backup as '+restart_file_name+'\n')
            else:
                sys.stdout.write('Restart file is already the latest. \n')
            os.chdir(original_dir)