#!/usr/bin/python

import os
import sys
import networkx as nx
import matplotlib.pyplot as plt
import argparse

from mininet.net import Mininet
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.node import OVSController
from mininet.node import Controller
from mininet.node import RemoteController
from mininet.cli import CLI
sys.path.append("../../")
from pox.ext.jelly_pox import JellyfishController
from subprocess import Popen
from time import sleep, time

from topologies import JellyfishTopo, FatTreeTopo, DummyTopo

def test_ping(net):
    """
    Simple test to make sure all hosts in a topology
    can ping each other.
    """
    net.start()
    sleep(3)
    net.pingAll()
    net.stop()

parser = argparse.ArgumentParser()
parser.add_argument('-display', action='store_true')

if __name__ == '__main__':

    args = parser.parse_args()

    # Create topology
    #topo = JellyfishTopo(n=6, k=6)
    topo = DummyTopo()

    # Create Mininet network with a custom controller
    net = Mininet(topo=topo, host=CPULimitedHost, link = TCLink,
        controller=JellyfishController)

    # Run ping all experiment
    test_ping(net)

    # Display the topology
    if args.display:
        g = nx.Graph()
        g.add_nodes_from(topo.nodes())
        g.add_edges_from(topo.links())
        nx.draw(g, with_labels=True)
        plt.show()