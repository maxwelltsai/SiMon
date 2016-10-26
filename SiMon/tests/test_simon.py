from ..simon import SiMon
import os
import unittest
import subprocess

# instance a simulation_task

class TestSimon(unittest.TestCase):
    def test_interactive_mode(self):
        # execute only if run as a script
        s = SiMon()

        # test interactive mode
        s.build_simulation_tree()
        s.print_sim_status_overview(0)

        # test choices without id input
        s.task_handler('l')

        with self.assertRaises(SystemExit):
            s.task_handler('q')

        '''
        with self.assertRaises(SystemExit) as cm:
            your_method()

        self.assertEqual(cm.exception.code, 1)
        '''

        # test choices requires id input
        self.selected_inst = 1  # test id

        # for choice in ['s', 'n', 'r', 'c', 'x', 'd', 'k', 'b', 'p']:
            # TODO: how to give an input here?
            # s.task_handler(choice)


    def test_daemon_mode(self):
        test_dir = os.path.join(os.path.dirname(__file__), 'test.sh')
        print('test dir', test_dir)
        subprocess.call([test_dir])
        # TODO: start and stop does not effect?