"""
Implementation of utilities used by SiMon globally.
"""

import sys
import os 
import glob 
import logging 
import configparser as cp 
from SiMon.config import DEFAULT_CONFIG as config 

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

__logger = None 

def get_simon_dir():
    return os.path.dirname(os.path.abspath(__file__))

def progress_bar(val, val_max, val_min=0, prefix="", suffix="", bar_len=20):
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
        return ""
    else:
        skipped_len = int(round(bar_len * val_min) / float(val_max))
        filled_len = int(round(bar_len * (val - val_min) / float(val_max)))
        # percents = round(100.0 * count / float(total), 1)
        bar = (
            "." * skipped_len
            + "|" * filled_len
            + "." * (bar_len - filled_len - skipped_len)
        )
        # return '[%s] %s%s %s\r' % (bar, percents, '%', suffix)
        return "%s [%s] %s\r" % (prefix, bar, suffix)

def highlighted_text(text, color=None, bold=False):
    colors = ["red", "blue", "cyan", "green", "yellow", "purple", "white", "reset"]
    color_codes = ["\033[31m", "\033[34m", "\033[36m", "\033[32m", "\033[0;33m", "\033[0;35m", "\033[0;37m", "\033[0m"]
    color_codes_bold = [
        "\033[1;31m",
        "\033[1;34m",
        "\033[1;36m",
        "\033[0;32m",
        "\033[1;33m",
        "\033[1;35m",
        "\033[1;37m",
        "\033[0;0m",
    ]

    if color not in colors:
        color = "reset"
    if bold is False:
        return "%s%s%s" % (
            color_codes[colors.index(color)],
            text,
            color_codes[colors.index("reset")],
        )
    else:
        return "%s%s%s" % (
            color_codes_bold[colors.index(color)],
            text,
            color_codes_bold[colors.index("reset")],
        )

def id_input(prompt):
    """
    Prompt to the user to input the simulation ID (in the interactive mode)
    """
    confirmed = False
    vec_index_selected = []
    while confirmed is False:
        response = get_input(prompt)
        fragment = response.split(",")
        for token_i in fragment:
            if "-" in token_i:  # it is a range
                limits = token_i.split("-")
                if len(limits) == 2:
                    try:
                        if int(limits[0].strip()) < int(limits[1].strip()):
                            subrange = range(
                                int(limits[0].strip()), int(limits[1].strip()) + 1
                            )
                            for j in subrange:
                                vec_index_selected.append(j)
                    except ValueError:
                        print("Invalid input. Please use only integer numbers.")
                        continue
            else:
                try:
                    int(token_i.strip())  # test integer
                    vec_index_selected.append(token_i.strip())
                except ValueError:
                    print(
                        "Invalid input %s. Please use only integer numbers."
                        % token_i.strip()
                    )
                    continue
        if (
            get_input(
                "Your input is \n\t" + str(vec_index_selected) + ", confirm? [Y/N] "
            ).lower()
            == "y"
        ):
            confirmed = True
            return list(map(int, vec_index_selected))
        else:
            vec_index_selected = []

def get_input(prompt_msg):
    """
    This method makes use of the raw_input() method in Python2 and input() method in Python 3.
    """
    return input(prompt_msg)

def generate_conf():
    try:
        target = open("SiMon.conf", "w")
        target.write(config_file_template)
        target.close()
    except IOError:
        print("Unexpected error:", sys.exc_info()[0])

def parse_config_file(config_file, section=None):
    """
    Parse the configure file (SiMon.conf) for starting SiMon. The basic information of Simulation root directory
    must exist in the configure file before SiMon can start. A minimum configure file of SiMon looks like:

    ==============================================
    [SiMon]
    Root_dir: <the_root_dir_of_the_simulation_data>
    ==============================================

    :return: return 0 if succeed, -1 if failed (file not exist, and cannot be created). If the file does not exist
    but a new file with default values is created, the method returns 1.
    """
    conf = cp.ConfigParser()
    if os.path.isfile(config_file):
        conf.read(config_file)
        if section is not None:
            if section in conf:
                return conf[section]
            else:
                raise ValueError('Section %s does not exist in config file %s.' % (section, config_file))
        else:
            return conf
    else:
        raise ValueError('Config file %s does not exist.' % (config_file))

def print_help():
    print("Usage: python simon.py [start|stop|interactive|help]")
    print(
        "\tTo show an overview of job status and quit: python simon.py (no arguments)"
    )
    print("\tstart: start the daemon")
    print("\tstop: stop the daemon")
    print("\tinteractive/i/-i: run in interactive mode (no daemon)")
    print("\thelp: print this help message")

def print_task_selector():
    """
    Prompt a menu to allow the user to select a task.

    :return: current selected task symbol.
    """
    opt = ""
    while opt.lower() not in [
        "l",
        "s",
        "n",
        "r",
        "c",
        "x",
        "t",
        "d",
        "k",
        "b",
        "p",
        "q",
    ]:
        sys.stdout.write("\n=======================================\n")
        sys.stdout.write(
            "\tList Instances (L), \n\tSelect Instance (S), "
            "\n\tNew Run (N), \n\tRestart (R), \n\tCheck status (C), "
            "\n\tStop Simulation (T), \n\tDelete Instance (D), \n\tKill Instance (K), "
            "\n\tBackup Restart File (B), \n\tPost Processing (P), \n\tUNIX Shell (X), "
            "\n\tQuit (Q): \n"
        )
        opt = get_input("\nPlease choose an action to continue: ").lower()

    return opt

def register_simon_modules(module_dir, user_shell_dir, module_pattern='module_*.py'):
    """
    Register modules
    :return: A dict-like mapping between the name of the code and the filename of the module.
    """
    mod_dict = dict()
    module_candidates = glob.glob(os.path.join(module_dir, module_pattern))
    module_cwd = glob.glob(
        os.path.join(user_shell_dir, module_pattern)
    )  # load the modules also from cwd
    for m_cwd in module_cwd:
        module_candidates.append(m_cwd)
    for mod_name in module_candidates:
        sys.path.append(module_dir)
        sys.path.append(os.getcwd())
        mod_name = os.path.basename(mod_name)
        mod = __import__(mod_name.split(".")[0])
        if hasattr(mod, "__simulation__"):
            # it is a valid SiMon module
            mod_dict[mod.__simulation__] = mod_name.split(".")[0]
    return mod_dict

def get_logger(log_level='INFO', log_dir=None, log_file='SiMon.log'):    
    if config['logger'] is not None:
        return config['logger']
    else:
        logger = logging.getLogger("DaemonLog")
        if log_level == "INFO":
            logger.setLevel(logging.INFO)
        elif log_level == "WARNING":
            logger.setLevel(logging.WARNING)
        elif log_level == "ERROR":
            logger.setLevel(logging.ERROR)
        elif log_level == "CRITICAL":
            logger.setLevel(logging.CRITICAL)
        else:
            logger.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "%(asctime)s - [%(levelname)s] - %(name)s - %(message)s"
        )

        if log_dir is None:
            log_dir = os.getcwd()
        handler = logging.FileHandler(os.path.join(log_dir, log_file))
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        config['logger'] = logger 
        return logger 