from ..simon import SiMon
import os
import unittest

class Test(unittest.TestCase):
    def test_simon(self):
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

        # for choice in ['s', 'd', 'k']  # TODO: 'r' 'x' mode has bugs now'

        # s.interactive_mode()