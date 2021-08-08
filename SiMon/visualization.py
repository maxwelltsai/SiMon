import os
import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import numpy as np
import math
from datetime import datetime
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.collections import LineCollection
from matplotlib import cm
from SiMon.simulation import Simulation
from SiMon.callback import Callback
from matplotlib.ticker import MaxNLocator
import time



class VisualizationCallback(Callback):

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def run(self):
        self.plot_progress()

    def plot_progress(self):
        """
        Creates a graph showing the progress of the simulations
        :param num_sim: number of simulations
        :return:
        """
        if 'container' in self.kwargs:
            sim_inst_dict = self.kwargs['container'].sim_inst_dict
        else:
            return 
        
        num_sim = len(sim_inst_dict)
        status = np.array([])
        progresses = np.array([])
        sim_idx = np.array([])
        for i, sim_name in enumerate(sim_inst_dict):
            sim = sim_inst_dict[sim_name]
            sim_id = sim.id 
            if sim_id == 0:
                continue # skip the root simulation instance, which is only a place holder
            
            # only plot level=1 simulations
            if sim.level > 1:
                continue

            s = sim.sim_get_status()
            if sim.t_max > 0:
                p = sim.t / sim.t_max
            else:
                p = 0.0
            status = np.append(s, status)
            progresses = np.append(p, progresses)
            sim_idx = np.append(sim_id, sim_idx)

        # Checks if num_sim has a square
        if int(math.sqrt(num_sim) + 0.5) ** 2 == num_sim:
            number = int(math.sqrt(num_sim))
            y_num = num_sim // number

        # If not square, find divisible number to get rectangle
        else:
            number = int(math.sqrt(num_sim))
            while num_sim % number != 0:
                number = number - 1
            y_num = num_sim // number                               # Y-axis limit

            # If prime number
            if number == 1:
                number = int(math.sqrt(num_sim)) + 1                # Make sure graph fits all num_sim
                y_num = number
                # 'Removes' extra white line if graph is too big
                if (y_num * number) > num_sim and ((y_num - 1) * number) >= num_sim:
                    y_num = y_num - 1

        x_sim = sim_idx % number
        y_sim = sim_idx // number

        plt.figure(1, figsize=(12, 12))
        ax = plt.gca()                                          # get the axis
        ax.set_ylim(ax.get_ylim()[::-1])                        # invert the axis
        ax.xaxis.tick_top()                                     # and move the X-Axis
        ax.yaxis.set_ticks(np.arange(-0.5, y_num))              # set y-ticks
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))   # set to integers
        ax.yaxis.tick_left()                                    # remove right y-Ticks

        symbols = ['o', 's', '>',  '^', '*',  'x']
        labels = ['NEW', 'STOP', 'RUN', 'STALL', 'DONE', 'ERROR']

        
        for i, symbol in enumerate(symbols):
            if (status == i).sum() == 0:
                continue
            else:
                plt.scatter(
                    x_sim[status == i],
                    y_sim[status == i],
                    marker=symbol,
                    s=500,
                    c=progresses[status == i],
                    cmap=cm.RdYlBu,
                    vmin = 0., vmax = 1.,
                    label=labels[i])

        for i in range(sim_idx.shape[0]):
            plt.annotate(
                text=str(sim_inst_dict[i].id),
                xy=(x_sim[i], y_sim[i]),
                color='black',
                weight='bold',
                size=15
            )

        plt.legend(
            bbox_to_anchor=(0., -.15, 1., .102),
            loc='lower center',
            ncol=4,
            mode="expand",
            borderaxespad=0.,
            borderpad=2,
            labelspacing=3
        )

        plt.colorbar()

        # # Save file with a new name
        # if os.path.exists('progress.pdf'):
        #     plt.savefig('progress_{}.pdf'.format(int(time.time())))
        # else:
        #     print('saving figure')
        if 'plot_dir' in self.kwargs:
            plot_dir = self.kwargs['plot_dir']
        else:
            plot_dir = os.getcwd()

        if not os.path.isdir(plot_dir):
            os.mkdir(plot_dir)

        fn = datetime.now().strftime("%d_%m_%Y-%H_%M_%S")
        if 'format' in self.kwargs:
            fmt = self.kwargs['format']
        else:
            fmt = 'png'
        fullpath = os.path.join(plot_dir, '%s.%s' % (fn, fmt))
        print('Progress plot saved on %s' % fullpath)
        plt.savefig(fullpath)
        plt.close(1)