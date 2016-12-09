from simulation_task import SimulationTask
import os
import sys
import re
import glob
import shutil
import numpy as np
import time
import signal

__simulation__ = 'Nbody6'  # should be the same as the class name


class Nbody6(SimulationTask):
    """
    Implementation for NBODY6 (Aarseth).
    """


    def __init__(self, sim_id, name, full_dir, status, mode='daemon', t_min=0, t_max=0, restarts=None):
        super(Nbody6, self).__init__(sim_id, name, full_dir, status, mode, t_min, t_max, restarts)
        self.t_min, self.t_max = self.sim_get_status()

    def sim_start(self):
        """
        Start a new Nbody6 simulation,
        """
        sys.stdout.write("Starting %s\n" % self.full_dir)
        # for each instance processing, there is a process.pid file, which contains a number
        # later process.pid will be overwrote or created by run.sh - os.system('sh run.sh')
        #
        # late line on run.sh:
        # ../../nbody6 < input 1>output.log 2>output.err  & echo $! > process.pid
        if os.path.isfile(os.path.join(self.full_dir, 'process.pid')):
            try:
                fpid = open(os.path.join(self.full_dir, 'process.pid'), 'r')
                pid = int(fpid.readline())
                fpid.close()
                if pid > 0:
                    os.kill(pid, 0)  # test if process exist, if not then an OSError will pop up
                    sys.stdout.write('WARNING: the instance is already running. Will not start new run.\n')
                    return
            except (ValueError, OSError):  # the instance is not running, can start a new instance
                os.chdir(self.full_dir)
                # scan and remove any previous restarting dirs

                # a restart dir is created for restoring new restart result, without overwirte previous ones
                # coz the restart will start from the crashed point eg.[T=20]
                restart_dir = glob.glob('restart*/')
                for r_dir in restart_dir:
                    shutil.rmtree(r_dir)
                os.system('sh run.sh')
                os.chdir('..')
        else:
            os.chdir(self.full_dir)
            # scan and remove any previous restarting dirs
            restart_dir = glob.glob('restart*/')
            for r_dir in restart_dir:
                shutil.rmtree(r_dir)
            os.system('sh run.sh')
            os.chdir('..')

    def check_instance_error_type(self):
        """
        Check the error type of an NBODY6 simulation from the tail of NBODY6 output.

        :return: return error type
        :type: string
        """
        errortype = ''

        # check output log for error type info
        if os.path.isfile(os.path.join(self.full_dir, 'output.log')):
            flog = open(os.path.join(self.full_dir, 'output.log'), 'r')
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
                ferr = open(os.path.join(self.full_dir, 'output.err'), 'r')
                line = ferr.readline()
                last_line = line
                while line != '':
                    line = ferr.readline()
                    if line != '':
                        lastline = line
                ferr.close()
                try:
                    errortype = last_line.strip()
                except UnboundLocalError:
                    errortype = 'unknown'
        else:
            errortype = 'unknown'

        return errortype

    def check_instance_hanged(self, inst_id):
        """
        Check if a simulation is hung.

        Sometimes, due to numerical difficulties (e.g. numerical singularity), the code
        becomes so slow that it does not make any progress for a long period of time.
        In such case, it is important to identify this behavior, kill the code, modify the
        time step parameters accordingly and then restart the code.
        """
        hanged = False
        if os.path.isfile(os.path.join(self.full_dir, 'process.pid')):
            try:
                fpid = open(os.path.join(self.full_dir, 'process.pid'), 'r')
                pid = 0
                try:
                    pid = int(fpid.readline())
                except ValueError:
                    sys.stdout.write('Error reading pid file for instance %d\n' % inst_id)
                fpid.close()
                if pid > 0:
                    os.kill(pid, 0)  # test if process exist

                # Exist, then test the file activity
                if os.path.isfile(os.path.join(self.full_dir, 'output.log')):
                    mtime = os.stat(os.path.join(self.full_dir, 'output.log')).st_mtime
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

    def sim_get_status(self):
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
            mtime = os.stat(os.path.join(self.full_dir, 'output.log')).st_mtime
            flog = open(os.path.join(self.full_dir, 'output.log'))
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

    def sim_clean(self):
        return super(Nbody6, self).sim_clean()

    def sim_delete(self):
        """
        Delete a simulation directory with all its data,
        including all the subdirectory created through restarting.
        """

        if self.mode == 'interactive':
            confirm = raw_input('Are you sure you would like to delete the instance '
                                '#%d and its sub-instances? [Y/N] ' % self.id).lower()
            if confirm != 'y':
                return 1
        else:
            # TODO: code will not goes here because no functions in daemon mode will call inst_delete
            shutil.rmtree(self.full_dir)
            return 0

    def sim_backup_checkpoint(self):
        # min and max T
        t_min, t_max = self.sim_get_status()
        original_dir = os.getcwd()
        os.chdir(self.full_dir)
        restart_file_list = glob.glob('restart.tmp.*')
        need_backup = True

        for rf in restart_file_list:  # string of restart file name
            if str(t_max) in rf:
                # if the simulation process doesn't make progress since last back up
                # then the backup file is already the latest one, no need to back up
                need_backup = False
                break

        if need_backup:
            restart_file_name = 'restart.tmp.' + str(t_max)
            if os.path.isfile('restart.tmp'):
                shutil.copyfile('restart.tmp', restart_file_name)
            elif os.path.isfile('restart.prev'):
                shutil.copyfile('restart.prev', restart_file_name)
            sys.stdout.write('Restart file has been backup as ' + restart_file_name + '\n')
        else:
            sys.stdout.write('Restart file is already the latest. \n')
        os.chdir(original_dir)

    def sim_init(self):
        return super(Nbody6, self).sim_init()

    def sim_finalize(self):
        return super(Nbody6, self).sim_finalize()

    def sim_reset(self):
        return super(Nbody6, self).sim_reset()

    def sim_restart(self):
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
        # Retrieve a list of restart files
        original_dir = os.getcwd()
        os.chdir(self.full_dir)
        rfiles = glob.glob('restart.tmp.*')  # * here stands for time
        os.chdir(original_dir)

        try:
            # last time of backing up the restart file
            rfile_list = sorted(rfiles, key=lambda fn: int(fn.split('.')[2]))
        except ValueError, e:
            print e
            rfile_list = sorted(rfiles)

        # Retrieve a list of restart directories
        rdir_list = glob.glob(os.path.join(self.full_dir, 'restart*/'))

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
            restart_dir_name = 'restart' + str(len(rdir_list) + 1)
            restart_file_name = os.path.join(self.full_dir, rfile_list[len(rfile_list) - 1 - len(rdir_list)])
            sys.stdout.write('The file %s will be used for restart.\n' % restart_file_name)
        else:
            sys.stderr.write('ERROR [SEVERE]: unable to proceed the simulation %s\n' % self.full_dir)
            fnorestart = open(os.path.join(self.full_dir, 'NORESTART'), 'w')
            fnorestart.write('NORESTART')
            fnorestart.close()
            return

        # check error type to restart accordingly
        errortype = self.check_instance_error_type()
        os.chdir(self.full_dir)
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
            d_name = self.full_dir
            # TODO: ignore pot_type
            pot_type = ''
            if 'pm' in d_name:
                pot_type = 'pm'
            elif 'iso' in d_name:
                pot_type = 'iso'
            elif 'power' in d_name:
                pot_type = 'power'
            f_restart.write(restart_script_template % (self.id % 4, '../' * (self.level + 1), pot_type))
            f_restart.close()

        # create input file for restart
        input_file = open(os.path.join(restart_dir_name, 'input'), 'w')
        sys.stdout.write('Instance error type: ' + errortype + '\n')

        # create a new restart input file according to error type
        restart_file_text = self.smart_restart(errortype)
        sys.stdout.write(restart_file_text + '\n')
        input_file.write(restart_file_text)
        input_file.close()

        os.chdir(restart_dir_name)
        os.system('sh run.sh')
        os.chdir('../..')

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

    def sim_shell_exec(self, shell_command=None):
        """
        Allow the user to execute a UNIX command in the directory of the currently active simulation instance.
        """
        if shell_command is None:
            shell_command = raw_input('CMD>> ')
        sys.stdout.write('========== Command on #%d ==> %s (PWD=%s) ==========\n'
                         % (self.id, self.full_dir, self.full_dir))
        original_dir = os.getcwd()
        os.chdir(self.full_dir)
        os.system(shell_command)
        sys.stdout.write('========== [DONE] Command on #%d ==> %s (PWD=%s) ==========\n'
                         % (self.id, self.full_dir, self.full_dir))
        os.chdir(original_dir)
        return 0

    def sim_stop(self):
        return super(Nbody6, self).sim_stop()

    def sim_kill(self):
        """
        Kill the UNIX process of a simulation.
        """
        if os.path.isfile(os.path.join(self.full_dir, 'process.pid')):
            fpid = open(os.path.join(self.full_dir, 'process.pid'), 'r')
            pid = 0
            try:
                pid = int(fpid.readline())
            except (ValueError, OSError), e:
                sys.stdout.write('Unable to kill instance #%d: unable to determine pid.\n' % self.id)
            fpid.close()
            if self.mode == 'interactive':
                confirm = raw_input('Are you sure you would like to kill the instance #%d? [Y/N] '
                                    % self.id).lower()
            else:
                try:
                    if pid > 0:
                        os.kill(pid, signal.SIGKILL)
                        sys.stdout.write('Instance %d [pid=%d] killed.\n' % (self.id, pid))
                except OSError, err:
                    sys.stdout.write('Cannot kill the process: \n' + str(err))
        else:  # TODO: here the else should be 'no process.pid file found'
            sys.stdout.write('Unable to kill instance #%d: unable to determine pid.\n' % self.id)

    def sim_collect_recent_output_message(self, lines=20):
        sys.stdout.write('========== Diagnose for #%d ==> %s ==========\n' % (self.id, self.full_dir))
        check_dir_name = self.full_dir
        original_dir = os.getcwd()
        os.chdir(check_dir_name)
        os.system('\ncat input')
        os.system('\ngrep ADJUST output.log | tail -%d' % lines)
        os.system('\ngrep "N =" output.log | tail -%d' % lines)
        os.system('\ntail -10 output.log')
        restart_dir = sorted(glob.glob('restart*/'))
        for r_dir in restart_dir:
            os.chdir(r_dir)
            sys.stdout.write('========== Diagnose for restart ==> %s ==========\n' % r_dir)
            os.system('\ncat input')
            os.system('\ngrep ADJUST output.log | tail -%d' % lines)
            os.system('\ngrep "N =" output.log | tail -%d' % lines)
            os.system('\ntail -%lines output.log' % lines)
            os.chdir('..')
        os.chdir(original_dir)
