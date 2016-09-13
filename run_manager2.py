import os
import os.path
import glob
from fnmatch import fnmatch
import time
import datetime
import sys
import shutil
import re
import numpy as np
import signal

sim_dir = '/Users/maxwell/Works/nbody6/Ncode/run'

class SimulationInstance(object):
    def __init__(self, id, name, fulldir, status, t_min = 0, t_max = 0, restarts = None):
        self.id = id
        self.name = name # usually the name of the simulation directory
        self.fulldir = fulldir # the full path of the simulation directory
        self.status = status # RUN, STOP, RESTARTED
        self.errortype = ''
        self.t_min = t_min
        self.t_max = t_max
        self.t_max_extended = t_max # extended t_max by restarts
        self.mtime = 0
        self.ctime = 0
        self.cid = -1 # the candidate instance ID to restart in case crashes
                      # (-1: no candidate, restart from itself;)
                      # (>0: restart from the candidate. If the candidate cannot restart, try siblings)
        self.level = 0
        self.parent_id = -1
        if restarts == None:
            self.restarts = list()
        else:
            self.restarts = restarts # children


    def __repr__(self, level=0):
        placeholder_dash = "|---"+'-'*(level*4)
        placeholder_space = "    "+' '*(level*4)
        ctime_str = datetime.datetime.fromtimestamp(self.ctime).strftime('%Y-%m-%d %H:%M:%S')
        mtime_str = datetime.datetime.fromtimestamp(self.mtime).strftime('%Y-%m-%d %H:%M:%S')
        info = "%s\t%s\t%s\n%s%s\tT=[%d-%d]\t%s\tCID=%d\tlevel=%d" % (repr(self.name), ctime_str, mtime_str,
                placeholder_space, self.status, self.t_min, self.t_max, self.errortype,self.cid,self.level)
        ret = "%d%s%s\n" % (self.id, placeholder_dash, info)
        #ret = "    "*level+str(self.id)+repr(self.name)+"\n"
        for child in self.restarts:
            ret += child.__repr__(level+1)
        return ret





class Run_Manager():

    def __init__(self, pidfile=None, stdin='/dev/tty', stdout='/dev/tty', stderr='/dev/tty',
            mode='interactive', cwd = sim_dir):
        self.selected_inst = None
        self.id_dict = None
        self.id_dict_short = None
        self.sim_inst_dict = None
        self.sim_inst_parent_dict = None
        self.sim_tree = SimulationInstance(0, 'root', cwd, 'STOP')
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






    def id_input(self, prompt):
        confirmed = False
        while confirmed == False:
            ids = raw_input(prompt).split(',')
            if raw_input('Your input is \n\t'+str(ids)+', confirm? [Y/N] ').lower() == 'y':
                confirmed = True
                return ids



    def traverse_dir(self):
        id_dict = dict()
        id_dict_short = dict()
        id = 0
        self.sim_tree = SimulationInstance(0, 'root', '.', 'STOP')
        run_dir = sorted(glob.glob('t_*')) # list root run_dir
        pattern = 'restart*'
        for d_path in run_dir:
            id += 1
            id_dict[id] = d_path
            id_dict_short[id] = d_path
            inode = SimulationInstance(id, d_path, d_path, 'STOP')
            self.sim_tree.restarts.append(inode)
            for root, dirs, files in os.walk(d_path):
                dirs = sorted(dirs)
                for dirname in fnmatch.filter(dirs, pattern):
                    id += 1
                    id_dict[id] = os.path.join(root, dirname)
                    id_dict_short[id] = dirname
                    isubnode = SimulationInstance(id, dirname, id_dict[id], 'STOP')
                    #inode.restarts.append(isubnode)

        return id_dict, id_dict_short


    def traverse_dir2(self, pattern, dir, files):
        for filename in sorted(files):
            if fnmatch(filename, pattern):
                if os.path.isdir(os.path.join(dir, filename)):
                    fullpath = os.path.join(dir, filename)
                    self.inst_id += 1
                    id = self.inst_id
                    self.id_dict[id] = fullpath
                    self.id_dict_short[id] = filename
                    sim_inst = SimulationInstance(id, filename, fullpath, 'STOP')
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
        os.chdir(self.cwd)
        self.id_dict = dict()
        self.id_dict_short = dict()
        self.sim_inst_dict = dict()
        self.sim_inst_parent_dict = dict()
        self.status_dict = dict()
        self.sim_tree = SimulationInstance(0, 'root', self.cwd, 'STOP')
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
        t_list = []
        try:
            mtime = os.stat(os.path.join(sim_dir, 'output.log')).st_mtime
            flog = open(os.path.join(sim_dir, 'output.log'))
            regex = re.compile('^ T = +([^,]\d+)')
            line = flog.readline()
            while line != '':
                res = regex.findall(line)
                if len(res)>0:
                    t_list.append(int(res[0]))
                line = flog.readline()
            flog.close()
        except OSError:
            mtime = 'NaN'
        if len(t_list)>0:
            return np.min(t_list), np.max(t_list)
        else:
            return 0, 0


    def task_selector(self):
        opt = ''
        while opt.lower() not in ['l', 's', 'n', 'r', 'c', 'x', 'd', 'k', 'b', 'p', 'q']:
            sys.stdout.write('\n=======================================\n')
            sys.stdout.write('\tList Instances (L), \n\tSelect Instance (S), \n\tNew Run (N), \n\tRestart (R), \n\tCheck status (C), \n\tExecute (X), \n\tDelete Instance (D), \n\tKill Instance (K), \n\tBackup Restart File (B), \n\tPost Processing (P), \n\tQuit (Q): \n')
            opt = raw_input('\nPlease choose an action to continue: ').lower()

        return  opt




    def task_handler(self, opt):

        if opt == 'q':
            sys.exit(0)
        elif opt == 'l':
            self.gen_instance_list()
        elif opt == 's':
            self.selected_inst = self.id_input('Please specify a list of IDs: ')
            sys.stdout.write('Instances ' + str(self.selected_inst) + ' selected.\n')
        elif opt == 'n':
            if self.mode == 'interactive':
                if self.selected_inst == None or len(self.selected_inst)==0:
                    self.selected_inst = self.id_input('Please specify a list of IDs: ')
                    sys.stdout.write('Instances ' + str(self.selected_inst) + ' selected.\n')
            self.inst_start_new()
        elif opt == 'r':
            if self.mode == 'interactive':
                if self.selected_inst == None or len(self.selected_inst)==0:
                    self.selected_inst = self.id_input('Please specify a list of IDs: ')
                    sys.stdout.write('Instances ' + str(self.selected_inst) + ' selected.\n')
            self.inst_restart()
        elif opt == 'c':
            if self.mode == 'interactive':
                if self.selected_inst == None or len(self.selected_inst)==0:
                    self.selected_inst = self.id_input('Please specify a list of IDs: ')
                    sys.stdout.write('Instances ' + str(self.selected_inst) + ' selected.\n')
            self.inst_check()
        elif opt == 'x':
            if self.mode == 'interactive':
                if self.selected_inst == None or len(self.selected_inst)==0:
                    self.selected_inst = self.id_input('Please specify a list of IDs: ')
                    sys.stdout.write('Instances ' + str(self.selected_inst) + ' selected.\n')
            self.inst_exec()
        elif opt == 'd':
            if self.mode == 'interactive':
                if self.selected_inst == None or len(self.selected_inst)==0:
                    self.selected_inst = self.id_input('Please specify a list of IDs: ')
                    sys.stdout.write('Instances ' + str(self.selected_inst) + ' selected.\n')
            self.inst_delete()
        elif opt == 'k':
            if self.mode == 'interactive':
                if self.selected_inst == None or len(self.selected_inst)==0:
                    self.selected_inst = self.id_input('Please specify a list of IDs: ')
                    sys.stdout.write('Instances ' + str(self.selected_inst) + ' selected.\n')
            self.inst_kill()
        elif opt == 'b':
            if self.mode == 'interactive':
                if self.selected_inst == None or len(self.selected_inst)==0:
                    self.selected_inst = self.id_input('Please specify a list of IDs: ')
                    sys.stdout.write('Instances ' + str(self.selected_inst) + ' selected.\n')
            self.inst_backup()
        elif opt == 'p':
            if self.mode == 'interactive':
                if self.selected_inst == None or len(self.selected_inst)==0:
                    self.selected_inst = self.id_input('Please specify a list of IDs: ')
                    sys.stdout.write('Instances ' + str(self.selected_inst) + ' selected.\n')
            for inst_id in self.selected_inst:
                self.convert_out3_to_hdf5(int(inst_id))



    def inst_start_new(self):

        for s in self.selected_inst:
            s = int(s)
            sys.stdout.write("Starting #%d ==> %s\n" % (s, self.id_dict[s]))
            if os.path.isfile(os.path.join(self.id_dict[s], 'process.pid')):
                try:
                    fpid = open(os.path.join(self.id_dict[s], 'process.pid'), 'r')
                    pid = 0
                    pid = int(fpid.readline())
                    fpid.close()
                    if pid > 0:
                        os.kill(pid, 0) # test if process exist
                        sys.stdout.write('WARNING: the instance is already running. Will not start new run.\n')
                        return
                except (ValueError,OSError), e:
                    # the instance is not running, can restart
                    os.chdir(self.id_dict[s])
                    # scan and remove any previous restarting dirs
                    restart_dir = sorted(glob.glob('restart*/'))
                    for r_dir in restart_dir:
                        shutil.rmtree(r_dir)
                    #proc = subprocess.Popen(['/bin/sh', self.id_dict[s]])
                    os.system('sh run.sh')
                    os.chdir('..')
            else:
                os.chdir(self.id_dict[s])
                # scan and remove any previous restarting dirs
                restart_dir = sorted(glob.glob('restart*/'))
                for r_dir in restart_dir:
                    shutil.rmtree(r_dir)
                #proc = subprocess.Popen(['/bin/sh', self.id_dict[s]])
                os.system('sh run.sh')
                os.chdir('..')
        # reset the selected instance
        self.selected_inst = None

    def inst_restart(self):
        restart_script_template = """touch 'start_time'
        export OMP_NUM_THREADS=2
        export GPU_LIST="%d"
        rm fort.* OUT* ESC COLL COAL data.h5part
        ../../nbody6 < input 1>output.log 2>output.err &
        echo $! > process.pid
        """

        for r in self.selected_inst:
            r = int(r)
            sys.stdout.write("Restarting #%d ==> %s\n" % (r, self.id_dict[r]))
            # Retrieve a list of restart files
            original_dir = os.getcwd()
            os.chdir(self.id_dict[r])
            rfiles = glob.glob('restart.tmp.*')
            os.chdir(original_dir)
            try:
                rfile_list = sorted(rfiles, key=lambda fn: int(fn.split('.')[2]))
            except ValueError, e:
                print e
                rfile_list = sorted(rfiles)
            # Retrieve a list of restart directories
            rdir_list = glob.glob(os.path.join(self.id_dict[r], 'restart*/'))
            restart_dir_name = ''
            restart_file_name = ''
            if len(rfile_list)>len(rdir_list):
                restart_dir_name = 'restart'+str(len(rdir_list)+1)
                restart_file_name = os.path.join(self.id_dict[r], rfile_list[len(rfile_list)-1-len(rdir_list)])
                sys.stdout.write('The file %s will be used for restart.\n' % restart_file_name)
            else:
                sys.stderr.write('ERROR [SEVERE]: unable to proceed the simulation %s\n' % self.id_dict[r])
                fnorestart = open(os.path.join(self.id_dict[r], 'NORESTART'), 'w')
                fnorestart.write('NORESTART')
                fnorestart.close()
                return

            errortype = self.check_instance_error_type(r)
            os.chdir(self.id_dict[r])
            os.mkdir(restart_dir_name)
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
                pot_type = ''
                if 'pm' in d_name:
                    pot_type = 'pm'
                elif 'iso' in d_name:
                    pot_type = 'iso'
                elif 'power' in d_name:
                    pot_type = 'power'
                f_restart.write(restart_script_template % (r%4, '../'*(self.sim_inst_dict[r].level+1), pot_type))
                f_restart.close()
            input_file = open(os.path.join(restart_dir_name, 'input'), 'w')
            sys.stdout.write('Instance error type: ' + errortype + '\n')
            restart_file_text = self.smart_restart(errortype)
            sys.stdout.write(restart_file_text+'\n')
            input_file.write(restart_file_text)
            input_file.close()
            os.chdir(restart_dir_name)
            os.system('sh run.sh')
            os.chdir('../..')
        # reset the selected instance
        self.selected_inst = None

    def inst_check(self):

        for c in self.selected_inst:
            c = int(c)
            sys.stdout.write('========== Diagnose for #%d ==> %s ==========\n' % (c, self.id_dict[c]))
            check_dir_name = self.id_dict[c]
            original_dir = os.getcwd()
            os.chdir(check_dir_name)
            os.system('\ncat input')
            os.system('\ngrep ADJUST output.log | tail -10')
            os.system('\ngrep "N =" output.log | tail -10')
            os.system('\ntail -10 output.log')
            restart_dir = sorted(glob.glob('restart*/'))
            for r_dir in restart_dir:
                os.chdir(r_dir)
                sys.stdout.write('========== Diagnose for restart ==> %s ==========\n' % (r_dir))
                os.system('\ncat input')
                os.system('\ngrep ADJUST output.log | tail -10')
                os.system('\ngrep "N =" output.log | tail -10')
                os.system('\ntail -10 output.log')
                os.chdir('..')

            os.chdir(original_dir)


    def inst_exec(self, cmd=None):
        if cmd == None:
            cmd = raw_input('CMD>> ')
        for e in self.selected_inst:
            e = int(e)
            sys.stdout.write('========== Command on #%d ==> %s (PWD=%s) ==========\n' % (e, self.id_dict[e], self.id_dict[e]))
            original_dir = os.getcwd()
            os.chdir(self.id_dict[e])
            os.system(cmd)
            sys.stdout.write('========== [DONE] Command on #%d ==> %s (PWD=%s) ==========\n' % (e, self.id_dict[e], self.id_dict[e]))
            os.chdir(original_dir)

    def inst_delete(self):

        for d in self.selected_inst:
            d = int(d)
            if self.mode == 'interactive':
                confirm = raw_input('Are you sure you would like to delete the instance #%d and its sub-instances? [Y/N] ' % d).lower()
            else:
                confirm = 'y'

            if confirm == 'y':
                shutil.rmtree(self.id_dict[d])
            if self.mode == 'interactive':
                show = raw_input('Instance deleted. Show a new list of instances? [Y/N] ').lower()
            else:
                show = 'y'

                if show == 'y':
                    self.gen_instance_list()
                else:
                    sys.stdout.write('Instance deletion aborted.\n')
        # reset the selected instance
        self.selected_inst = None

    def inst_kill(self):

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
                    confirm = raw_input('Are you sure you would like to kill the instance #%d? [Y/N] ' % k).lower()
                else:
                    confirm = 'y'

                if confirm == 'y':
                    try:
                        if pid > 0:
                            os.kill(pid, signal.SIGKILL)
                            sys.stdout.write('Instance %d [pid=%d] killed.\n' % (k, pid))
                    except OSError, err:
                        sys.stdout.write('Cannot kill the process: \n' + str(err))
            else:
                sys.stdout.write('Unable to kill instance #%d: unable to determine pid.\n' % k)

        # reset the selected instance
        self.selected_inst = None

    def inst_backup(self):

        for b in self.selected_inst:
            b = int(b)
            inst_dir = self.id_dict[b]
            t_min, t_max = self.get_sim_status(inst_dir)
            original_dir = os.getcwd()
            os.chdir(inst_dir)
            restart_file_list = glob.glob('restart.tmp.*')
            need_backup = True
            for rf in restart_file_list:
                if str(t_max) in rf:
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

    def convert_out3_to_hdf5(self, inst_id):
        inst = self.sim_inst_dict[inst_id]
        original_path = os.getcwd()
        os.chdir(inst.fulldir)
        sim_path = []
        out3_path = ''
        while inst.cid != -1:
            sim_path.append(inst)
            out3_path = out3_path + ' ' + os.path.join(inst.fulldir, 'OUT3')
            inst = self.sim_inst_dict[inst.cid]
        sim_path.append(inst)
        out3_path = out3_path + ' ' + os.path.join(inst.fulldir, 'OUT3')

        # generate the out3_to_hdf5 script
        fout3 = open('convert_out3_to_hdf5.sh', 'w')
        shutil.copy('/user/epsguest/eps310/out3_to_hdf5.py', os.getcwd())
        shutil.copy('/user/epsguest/eps310/make_plots.py', os.getcwd())
        fout3.write("python out3_to_hdf5.py -f '%s'\n" % out3_path)
        fout3.write('PID=$!\n')
        fout3.write('wait $PID\n')
        fout3.write('python make_plots.py\n')
        fout3.write('PID=$!\n')
        fout3.write('wait $PID\n')
        fout3.write('cp out.hdf5.pdf ~/tt_plots/'+self.sim_inst_dict[inst_id].name+'.pdf')
        fout3.close()
        # execute the script
        os.system('sh convert_out3_to_hdf5.sh 1>out3.log 2>out3.err &')
        os.chdir(original_path)



    def check_instance_hanged(self, inst_id):
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
                    os.kill(pid, 0) # test if process exist

                # Exist, then test the file activity
                if os.path.isfile(os.path.join(inst_dir, 'output.log')):
                    mtime = os.stat(os.path.join(inst_dir, 'output.log')).st_mtime
                    if time.time()-mtime<7200:
                        hanged = False
                    else:
                        hanged = True
                else:  # log file not exist, cannot determine whether or not hanged
                    hanged = False
            except OSError, err: # process may not exist, then instance not running
                err = str(err)
                if err.find("No such process") > 0:
                    hanged = False
        else:  # pid not exist, cannot determine whether the instance is running or not
            hanged = False

        return hanged

    def check_instance_error_type(self, inst_id):
        errortype = ''
        inst_dir = self.id_dict[inst_id]
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


    def smart_restart(self, errortype):
        restart_file_text = ''
        if errortype == 'SMALL STEP':
            restart_file_text = '4 10000000.0\n0.03 0.02 0.02 0.0 0.0 0\n30000 0 0\n30000 0 0'
        elif errortype == 'CALCULATIONS HALTED':
            restart_file_text = '4 10000000.0\n0.01 0.01 0.01 0.0 0.0 0\n30000 0 0\n30000 0 0'
        else:
            restart_file_text = '4 10000000.0\n0.02 0.02 0.02 0.0 0.0 0\n30000 0 0\n30000 0 0'
        return restart_file_text


    def main(self):
        os.chdir(self.cwd)
        self.gen_instance_list()
        choice = ''
        while choice != 'q':
            choice = self.task_selector()
            self.task_handler(choice)


    def run(self):
        os.chdir(self.cwd)
        self.gen_instance_list()
        while True:
            print('Auto scheduled\n')
            self.auto_scheduler()
            sys.stdout.flush()
            sys.stderr.flush()
            time.sleep(300)


    def auto_scheduler(self):
        os.chdir(self.cwd)
        self.gen_instance_list()
        schedule_list = []
        max_concurrent_jobs = 5
        concurrent_jobs = 0
        for i in self.sim_inst_dict.keys():
            inst = self.sim_inst_dict[i]
            if 'RUN' in inst.status and inst.cid==-1:
                if os.path.isfile(os.path.join(inst.fulldir, 'process.pid')):
                    try:
                        fpid = open(os.path.join(inst.fulldir, 'process.pid'), 'r')
                        strpid = fpid.readline()
                        fpid.close()
                    except OSError:
                        pass
                    if strpid.strip() in inst.status:
                        try:
                            print 'Stripd = '+strpid
                            os.kill(int(strpid), 0)
                            concurrent_jobs += 1
                        except (OSError, ValueError), e:
                            pass

        print os.path.join(os.getcwd(),'schedule.job')
        if os.path.isfile(os.path.join(os.getcwd(),'schedule.job')):
            sfile = open(os.path.join(os.getcwd(),'schedule.job'))
            try:
                buf = sfile.readline()
                while buf != '':
                    schedule_list.append(buf.strip())
                    buf = sfile.readline()
                sfile.close()
            except Exception:
                sfile.close()
        print 'The following simulations scheudled: '+str(schedule_list)
        for i in self.status_dict.keys():
            if i == 0: # the root group, skip
                continue
            status = self.sim_inst_dict[i].status
            self.status_dict[i] = status
            d_name = self.id_dict[i]
            d_name_short = self.id_dict_short[i]
            print 'Checking instance #%d ==> %s' % (i, d_name)
            if 'RUN' in status:
                if 'HANG' in status:
                    self.selected_inst = []
                    self.selected_inst.append(i)
                    self.inst_kill()
                    self.gen_instance_list()
                    self.selected_inst = []
                else:
                    self.selected_inst = []
                    self.selected_inst.append(i)
                    self.inst_backup()
                    self.selected_inst = []
            elif 'STOP' in status:
                print 'STOP detected: '+d_name+str(concurrent_jobs)+' '+str(self.sim_inst_dict[i].level)
                t_min, t_max = self.get_sim_status(d_name)
                if self.tcrit-t_max <=100: # mark as finished
                    self.sim_inst_dict[i].status = 'DONE'
                else:
                    if t_max == 0 and d_name_short in schedule_list and concurrent_jobs < max_concurrent_jobs:
                        # Start new run
                        self.selected_inst = []
                        self.selected_inst.append(i)
                        self.inst_start_new()
                        self.selected_inst = []
                        concurrent_jobs += 1

                    elif concurrent_jobs < max_concurrent_jobs and self.sim_inst_dict[i].level==1:
                        # search only top level instance to find the restart candidate
                        # build restart path
                        current_inst = self.sim_inst_dict[i]
                        while current_inst.cid != -1:
                            current_inst = self.sim_inst_dict[current_inst.cid]

                        print 'RESTART: #%d ==> %s' % (current_inst.id, current_inst.fulldir)
                        self.selected_inst = []
                        self.selected_inst.append(current_inst.id)
                        self.inst_restart()
                        self.selected_inst = []
                        concurrent_jobs += 1





if __name__ == "__main__":
    Run_Manager().main()
