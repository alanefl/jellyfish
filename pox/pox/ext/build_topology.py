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
from subprocess import Popen
from time import sleep, time

# These two map strings to class constructors for
# controllers and topologies.
from pox.ext.controllers import controllers
from topologies import topologies

def test_ping(net):
    """
    Simple test to make sure all hosts in a topology
    can ping each other.
    """
    print("\n\n==== Running ping all test ...")
    net.start()
    sleep(3)
    net.pingAll()
    net.stop()


# Set up argument parser.

parser = argparse.ArgumentParser()
parser.add_argument('-display', action='store_true')
parser.add_argument('-c','--controller',
    help='What controller from pox.ext.controllers to use', required=True)

#TODO: we need to be able to give topology constructor arguments
#      from the command line.
parser.add_argument('-t','--topology',
    help='What topology from pox.ext.topologies to use', required=True)

if __name__ == '__main__':

    args = vars(parser.parse_args())

    topo = topologies[args['topology']]()

    # Create Mininet network with a custom controller
    net = Mininet(topo=topo, host=CPULimitedHost, link = TCLink,
        controller=controllers[args['controller']])

    # Run ping all experiment
    test_ping(net)

    # Display the topology
    if args['display']:
        g = nx.Graph()
        g.add_nodes_from(topo.nodes())
        g.add_edges_from(topo.links())
        nx.draw(g, with_labels=True)
        plt.show()