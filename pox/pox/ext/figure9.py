#!/usr/bin/python

import matplotlib.pyplot as plt
import time

import sys
sys.path.append("../../")
from pox.core import core
from topologies import JellyfishTopo
from routing import Routing

"""
Reproduce Figure 9 from https://people.inf.ethz.ch/asingla/papers/jellyfish-nsdi12.pdf
and save to 'figure9.png'
"""
log = core.getLogger()

def plot_line(topo, proto, label, color, linestyle='-', linewidth=2):
    start = time.time()

    routing = Routing(topo, proto, log)
    paths = routing.generate_random_permutation_paths()
    edge_counts = sorted(routing.edge_counts(paths).values())

    x = [0]
    y = [0]
    for i in range(len(edge_counts)):
        # format graph properly
        if i != 0 and edge_counts[i] != edge_counts[i-1]:
            x.append(i)
            y.append(edge_counts[i-1])
        x.append(i)
        y.append(edge_counts[i])
    y.append(edge_counts[-1] + 1)
    x.append(len(edge_counts) - 1)
    plt.plot(x, y, color=color, linestyle=linestyle,
        linewidth=linewidth, label=label)

    finish = time.time()
    log.info('{} ran in: {}'.format(label, finish - start))

def figure9():
    start = time.time()
    topo = JellyfishTopo(n=686, k=7)
    topo_build_time = time.time() - start
    log.info('Topology built in: {}'.format(topo_build_time))

    plt.grid(True)
    plt.ylabel('# Distinct Paths Link is on')
    plt.xlabel('Rank of Link')

    plot_line(topo, 'kshort', '8 Shortest Paths', 'blue', linewidth=7)
    plot_line(topo, 'ecmp8', '8-way ECMP', 'olive')
    plot_line(topo, 'ecmp64', '64-way ECMP', 'red', linestyle=':')

    plt.legend(loc=2)
    plt.savefig('figure9.png')

if __name__ == '__main__':
    figure9()
