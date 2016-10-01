import os
import sys
import time

from simon_mode_common import SiMon


class DaemonSiMon(SiMon):

    def __init__(self):
        super(DaemonSiMon, self).__init__(pidfile=os.path.join(os.getcwd(), 'run_mgr_daemon.pid'),
                                          stdin='/dev/tty',
                                          stdout=os.path.join(os.getcwd(), 'out'),
                                          stderr=os.path.join(os.getcwd(), 'err'),
                                          mode='daemon')

    def run(self):
        """
        The entry point of this script if it is run with the daemon.
        """
        os.chdir(self.cwd)
        self.gen_instance_list()
        while True:
            print('Auto scheduled\n')
            self.auto_scheduler()
            sys.stdout.flush()
            sys.stderr.flush()
            time.sleep(300)

    def auto_scheduler(self):
        """
        The automatic decision maker for the daemon.

        The daemon invokes this method at a fixed period of time. This method checks the
        status of all simulations by traversing to all simulation directories and parsing the
        output files. It subsequently deals with the simulation instance according to the informtion
        gathered.
        """
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