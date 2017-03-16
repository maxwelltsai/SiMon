import time
import numpy as np
from optparse import OptionParser

parser = OptionParser()
parser.add_option('-s', '--t_start', action='store', type='float', dest='t_start',
                  help='The termination time of the pseudo simulation')
parser.add_option('-t', '--t_end', action='store', type='float', dest='t_end',
                  help='The termination time of the pseudo simulation')
parser.add_option('-f', '--output_file', action='store', type='string', dest='out_file',
                  help='The file name of the output file')
parser.add_option('-o', '--omega', action='store', type='float', dest='o',
                  help='frequency')
parser.add_option('-a', '--amplitude', action='store', type='float', dest='a',
                  help='The semi-major axis')

t_start = 0.0
t_end = 10.0
out_file = 'output.txt'
a = 1.0
omega = 1.0

(options, args) = parser.parse_args()
if options.t_start is not None:
    t_start = options.t_start
if options.t_end is not None:
    t_end = options.t_end
if options.out_file is not None:
    out_file = options.out_file
if options.a is not None:
    a = options.a
if options.o is not None:
    omega = options.o

xx = np.linspace(t_start, t_end, 50*int(t_end))
yy = a*np.sin(omega*xx) + 0.05*a*np.random.rand(len(xx))

out_f = open(out_file, 'w')

for ind in range(len(xx)):
    print(xx[ind])
    out_f.write('%f, %f\n' % (xx[ind], yy[ind]))
    time.sleep(0.05)

out_f.close()
