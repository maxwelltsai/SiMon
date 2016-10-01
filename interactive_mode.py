import os
import sys
import time
import shutil

from simon_mode_common import SiMon


class InteractiveSiMon(SiMon):
    def __init__(self):
        super(InteractiveSiMon, self).__init__()

    def main(self):
        """
        The entry point of this script if it is run directory (i.e. without a daemon).
        """
        os.chdir(self.cwd)
        self.gen_instance_list()
        choice = ''
        while choice != 'q':
            choice = self.task_selector()
            self.task_handler(choice)

    def task_selector(self):
        """
        Prompt a menu to allow the user to select a task.

        :return: current selected task symbol.
        """
        opt = ''
        while opt.lower() not in ['l', 's', 'n', 'r', 'c', 'x', 'd', 'k', 'b', 'p', 'q']:
            sys.stdout.write('\n=======================================\n')
            sys.stdout.write('\tList Instances (L), \n\tSelect Instance (S), '
                             '\n\tNew Run (N), \n\tRestart (R), \n\tCheck status (C), '
                             '\n\tExecute (X), \n\tDelete Instance (D), \n\tKill Instance (K), '
                             '\n\tBackup Restart File (B), \n\tPost Processing (P), \n\tQuit (Q): \n')
            opt = raw_input('\nPlease choose an action to continue: ').lower()

        return opt

    def task_handler(self, opt):
        """
        Handles the task selection input from the user.

        :param opt: task unit symbol.
        """

        if opt == 'q':
            sys.exit(0)
        if opt == 'l':
            self.gen_instance_list()
        if opt in ['s', 'n', 'r', 'c', 'x', 'd', 'k', 'b', 'p']:
            if self.mode == 'interactive':
                if self.selected_inst == None or len(self.selected_inst)==0:
                    self.selected_inst = self.id_input('Please specify a list of IDs: ')
                    sys.stdout.write('Instances ' + str(self.selected_inst) + ' selected.\n')

        # TODO: use message? to rewrite this part in a smarter way
        if opt == 'n':
            self.inst_start_new()
        if opt == 'r':
            self.inst_restart()
        if opt == 'c':
            self.inst_check()
        if opt == 'x':
            self.inst_exec()
        if opt == 'd':
            self.inst_delete()
        if opt == 'k':
            self.inst_kill()
        if opt == 'b':
            self.inst_backup()
        if opt == 'p':
            for inst_id in self.selected_inst:
                self.convert_out3_to_hdf5(int(inst_id))

    # interactive mode specific
    def inst_check(self):
        """
        Check the status of the current simulation instance and output to terminal.
        """
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
                sys.stdout.write('========== Diagnose for restart ==> %s ==========\n'
                                 % (r_dir))
                os.system('\ncat input')
                os.system('\ngrep ADJUST output.log | tail -10')
                os.system('\ngrep "N =" output.log | tail -10')
                os.system('\ntail -10 output.log')
                os.chdir('..')

            os.chdir(original_dir)

    def inst_exec(self, cmd=None):
        """
        Allow the user to execute a UNIX command in the directory of the currently active simulation instance.
        """
        if cmd is None:
            cmd = raw_input('CMD>> ')
        for e in self.selected_inst:
            e = int(e)
            sys.stdout.write('========== Command on #%d ==> %s (PWD=%s) ==========\n'
                             % (e, self.id_dict[e], self.id_dict[e]))
            original_dir = os.getcwd()
            os.chdir(self.id_dict[e])
            os.system(cmd)
            sys.stdout.write('========== [DONE] Command on #%d ==> %s (PWD=%s) ==========\n'
                             % (e, self.id_dict[e], self.id_dict[e]))
            os.chdir(original_dir)

    # TODO: 1) difference between kill and delete 2) this will not apply to daemon?
    def inst_delete(self):
        """
        Delete a simulation directory with all its data,
        including all the subdirectory created through restarting.
        """
        for d in self.selected_inst:
            d = int(d)
            if self.mode == 'interactive':
                confirm = raw_input('Are you sure you would like to delete the instance '
                                    '#%d and its sub-instances? [Y/N] ' % d).lower()
                # TODO: use confirm to control delete or not, and limit to y/n input
            else:
                # TODO: code will not goes here because no functions in daemon mode will call inst_delete
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

    def convert_out3_to_hdf5(self, inst_id):
        """
        Convert the NBODY6 OUT3 data file to HDF5 file.

        Notes
        ------
        Nbody6 out3 file contains coordinate etc. info.
        """

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
