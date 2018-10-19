"""
Implementation of utilities used by SiMon globally.
"""

import sys


config_file_template = """# Global config file for SiMon
[SiMon]

# The simulation data root directory
Root_dir: examples/demo_simulations

# The time interval for the SiMon daemon to check all the simulations (in seconds) [Default: 180]
Daemon_sleep_time: 180

# The number of simulations to be carried out simultaneously [Default: 2]
Max_concurrent_jobs: 2

# The maximum number of times a simulation will be restarted (a simulation is marked as ERROR when exceeding this limit) [Default: 2]
Max_restarts: 2

# Log level of the daemon: INFO/WARNING/ERROR/CRITICAL [default: INFO]
Log_level: INFO

# The time (in seconds) since the last modification of the output file, beyond which a simulation is considered stalled
Stall_time: 7200
"""


class Utilities(object):

    @staticmethod
    def progress_bar(val, val_max, val_min=0, prefix='', suffix='', bar_len=20):
        """
        Displays a progress bar in the simulation tree.
        :param val: current value
        :param val_max: maximum value
        :param val_min: minimum value
        :param prefix: marker for the completed part
        :param suffix: marker for the incomplete part
        :param bar_len: total length of the progress bar
        :return: a string representation of the progressbar
        """
        if val_max == 0:
            return ''
        else:
            skipped_len = int(round(bar_len * val_min) / float(val_max))
            filled_len = int(round(bar_len * (val - val_min) / float(val_max)))
            # percents = round(100.0 * count / float(total), 1)
            bar = '.' * skipped_len + '|' * filled_len + '.' * (bar_len - filled_len - skipped_len)
            # return '[%s] %s%s %s\r' % (bar, percents, '%', suffix)
            return '%s [%s] %s\r' % (prefix, bar, suffix)

    @staticmethod
    def highlighted_text(text, color=None, bold=False):
        colors = ['red', 'blue', 'cyan', 'green', 'reset']
        color_codes = ['\033[31m', '\033[34m', '\033[36m', '\033[32m', '\033[0m']
        color_codes_bold = ['\033[1;31m', '\033[1;34m', '\033[1;36m', '\033[0;32m', '\033[0;0m']

        if color not in colors:
            color = 'reset'
        if bold is False:
            return '%s%s%s' % (color_codes[colors.index(color)], text, color_codes[colors.index('reset')])
        else:
            return '%s%s%s' % (color_codes_bold[colors.index(color)], text, color_codes_bold[colors.index('reset')])

    @staticmethod
    def id_input(prompt):
        """
        Prompt to the user to input the simulation ID (in the interactive mode)
        """
        confirmed = False
        vec_index_selected = []
        while confirmed is False:
            response = Utilities.get_input(prompt)
            fragment = response.split(',')
            for token_i in fragment:
                if '-' in token_i:  # it is a range
                    limits = token_i.split('-')
                    if len(limits) == 2:
                        try:
                            if int(limits[0].strip()) < int(limits[1].strip()):
                                subrange = range(int(limits[0].strip()), int(limits[1].strip())+1)
                                for j in subrange:
                                    vec_index_selected.append(j)
                        except ValueError:
                            print('Invalid input. Please use only integer numbers.')
                            continue
                else:
                    try:
                        int(token_i.strip())  # test integer
                        vec_index_selected.append(token_i.strip())
                    except ValueError:
                        print('Invalid input %s. Please use only integer numbers.' % token_i.strip())
                        continue
            if Utilities.get_input('Your input is \n\t'+str(vec_index_selected)+', confirm? [Y/N] ').lower() == 'y':
                confirmed = True
                return map(int, vec_index_selected)
            else:
                vec_index_selected = []

    @staticmethod
    def get_input(prompt_msg):
        """
        This method makes use of the raw_input() method in Python2 and input() method in Python 3.
        """
        if sys.version_info[:2] <= (2, 7):
            return raw_input(prompt_msg)
        else:
            return input(prompt_msg)

    @staticmethod
    def generate_conf():
        try:
            target = open('SiMon.conf', 'w')
            target.write(config_file_template)
            target.close()
        except IOError:
            print("Unexpected error:", sys.exc_info()[0])
