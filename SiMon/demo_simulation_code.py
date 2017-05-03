import os
import sys
import time
import numpy as np
from optparse import OptionParser

parser = OptionParser()
parser.add_option('-s', '--t_start', action='store', type='float', dest='t_start',
                  help='The termination time of the pseudo simulation')
parser.add_option('-t', '--t_end', action='store', type='float', dest='t_end',
                  help='The termination time of the pseudo simulation')
parser.add_option('-d', '--dt', action='store', type='float', dest='dt',
                  help='The time step of the pseudo simulation')
parser.add_option('-f', '--output_file', action='store', type='string', dest='out_file',
                  help='The file name of the output file')
parser.add_option('-o', '--omega', action='store', type='float', dest='o',
                  help='frequency')
parser.add_option('-a', '--amplitude', action='store', type='float', dest='a',
                  help='The semi-major axis')
parser.add_option('-p', '--crash_probability', action='store', type='float', dest='p_crash',
                  help='The probability for the code to crash [0-1]')

t_start = 0.0
t_end = 10.0
dt = 0.02
out_file = 'output.txt'
restart_file = 'restart.txt'
restart_freq = 50
a = 1.0
omega = 1.0
p_crash = 0.001

(options, args) = parser.parse_args()
if options.t_start is not None:
    t_start = options.t_start
if options.t_end is not None:
    t_end = options.t_end
if options.dt is not None:
    dt = options.dt
if options.out_file is not None:
    out_file = options.out_file
if options.a is not None:
    a = options.a
if options.o is not None:
    omega = options.o
if options.p_crash is not None:
    p_crash = options.p_crash

if os.path.isfile(restart_file):
    f_restart = open(restart_file, 'r')
    t_start = float(f_restart.read())
    f_restart.close()

xx = np.arange(t_start, t_end+dt, dt)
yy = a*np.sin(omega*xx) + 0.05*a*np.random.rand(len(xx))

out_f = open(out_file, 'wb')

for ind in range(len(xx)):
    print(xx[ind])
    out_f.write('%f, %f\n' % (xx[ind], yy[ind]))
    if (ind != 0 and ind % restart_freq == 0) or (ind == len(xx) - 1):
        f_restart = open(restart_file, 'w')
        f_restart.write('%f' % xx[ind])
        f_restart.close()
        # if a STOP file is present in the current directory, stop the demo simulation
        if os.path.isfile('STOP'):
            sys.exit(0)
    time.sleep(0.05)
    if np.random.rand() < p_crash:
        # print('Code crashed!')
        sys.exit(-1)

out_f.close()
