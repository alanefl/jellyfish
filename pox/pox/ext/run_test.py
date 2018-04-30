#!/usr/bin/python

import os
import sys
import networkx as nx
import matplotlib.pyplot as plt
import argparse
import random

from mininet.net import Mininet
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.node import OVSController
from mininet.node import Controller
from mininet.node import RemoteController
from mininet.cli import CLI
from mininet.util import custom, pmonitor
sys.path.append("../../")
from subprocess import Popen
from time import sleep, time

# These two map strings to class constructors for
# controllers and topologies.
from pox.ext.controllers import JellyfishController
from topologies import topologies

def test_ping(net):
    """
    Simple test to make sure all hosts in a topology
    can ping each other.
    """
    print("\n\n==== Running ping all test ...")

    try:
        net.start()
        sleep(3)
        net.pingAll()
    except KeyboardInterrupt:
        pass
    finally:
        net.stop()

def get_permutation_traffic_dict(hosts):
    """
    Returns a dictionary that specifies what host
    should send traffic to what host:

        hx --> hy

    """
    hosts_ = hosts[:]
    send_dict = {}
    for h in hosts:
        send_idx = random.choice(range(len(hosts_)))
        send_dict[h] = hosts_[send_idx]
        del hosts_[send_idx]
    return send_dict


def update_server_throughputs(host_lines, host_throughput, rounds):
    for h in host_lines:
        if h not in host_throughput:
            host_throughput[h] = 0
        host_throughput[h] += float(host_lines[h].split()[-2]) / rounds

def monitor_throughput(popens, P, rounds, host_throughput):
    """
    Prints process information from different network hosts.
    See: https://github.com/mininet/mininet/blob/master/examples/popen.py

    The purpose of this is to catch the throughput measurements of
    the various iperf tasks.
    """
    host_lines = {}
    for host, line in pmonitor(popens):
        if host:

            # Catch the lines of output we care about
            if P == 1:
                if 'Bytes' in line:
                    host_lines[host.name] = line.strip()
            else:
                if '[SUM]' in line:
                    host_lines[host.name] = line.strip()
            print("<%s>: %s" % (host.name, line.strip()))

    # Update the per-server throughput values
    update_server_throughputs(host_lines, host_throughput, rounds)

def rand_perm_traffic(net, P=1, rounds=5):
    """
    Tests the topology using random permutation traffic,
    as descibed in the Jellyfish paper.

        P is the number of parallel flows to send from each host
        to another host.
    """
    send_dict = get_permutation_traffic_dict(net.topo.hosts())
    host_throughput = {}

    try:
        net.start()
        for i in range(rounds):
            print(" \n ROUND %d \n" % (i+1))
            popens = {}
            for h in send_dict:
                from_host_name = h
                to_host_name = send_dict[h]
                from_host, to_host = net.getNodeByName(from_host_name, to_host_name)
                from_ip = from_host.IP()
                to_ip = to_host.IP()
                #print("\n=== Sending from %s:%s to %s:%s" % (from_host_name, from_ip, to_host_name, to_ip))

                # Set iperf server on target host
                to_host.popen('iperf -s')

                # Set an iperf client on client host
                popens[from_host] = from_host.popen('iperf -c %s -P %s' % (to_ip, P))

            # Get the output from the iperf commands.
            monitor_throughput(popens, P, rounds, host_throughput)

    except KeyboardInterrupt:
        pass
    finally:
        net.stop()
        print(host_throughput) # values in GBits/s

# Set up argument parser.

parser = argparse.ArgumentParser()
parser.add_argument('-display', action='store_true')
parser.add_argument('-pingtest', action='store_true')
parser.add_argument('-randpermtraffic', action='store_true')


#TODO: we need to be able to give topology constructor arguments
#      from the command line.
parser.add_argument('-t','--topology',
    help='What topology from pox.ext.topologies to use', required=True)
parser.add_argument('-f','--flows',
    help='Number of flows to test with random permutation traffic')


if __name__ == '__main__':

    args = vars(parser.parse_args())

    # TODO (nice to have): propagate this to both, instead of hardcoding it
    random_seed = None
    topo = topologies[args['topology']]()

    # Create Mininet network with a custom controller
    net = Mininet(topo=topo, controller=JellyfishController)#, host=CPULimitedHost, link=TCLink) TODO: why do these arguments fail?

    if args['pingtest']:
        # Run ping all experiment
        test_ping(net)
    elif args['randpermtraffic']:
        # Random permutation traffic test
        P = 1
        if 'flows' in args:
            P = int(args['flows'])
        rand_perm_traffic(net, P=P)

    # Display the topology
    if args['display']:
        print("\n\n==== Displaying topology ...")
        g = nx.Graph()
        g.add_nodes_from(topo.nodes())
        g.add_edges_from(topo.links())
        nx.draw(g, with_labels=True)
        plt.show()