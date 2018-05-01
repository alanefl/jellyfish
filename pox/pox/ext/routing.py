#!/usr/bin/python

from collections import defaultdict
from functools import partial
import networkx as nx
import itertools
import random

from topologies import dpid_to_mac_addr, node_name_to_dpid
import pox.openflow.libopenflow_01 as of

import yens

class Routing():
    def __init__(self, topo, rproto, log):
        self.topo = topo
        self.set_path_fn(rproto)

        self.mac_to_hostname = {} # Maps host MAC addresses to hostnames.
        for host in topo.hosts():
            self.mac_to_hostname[dpid_to_mac_addr(node_name_to_dpid(host))] = host
        self.log.info(self.mac_to_hostname)

    def set_path_fn(self, rproto):
        self.path_fn = None

        if rproto == 'kshort': # use 8 as k
            self.path_fn = partial(self.k_shortest_paths, k=8)
        elif rproto == 'ecmp8':
            self.path_fn = partial(self.ecmp_paths, k=8)
        elif rproto == 'ecmp64':
            self.path_fn = partial(self.ecmp_paths, k=64)

        if not self.path_fn: raise Exception('Unknown routing protocol')

    def generate_rtable(self):
        self.rtable = self.generate_dports(topo, path_fn)

    def k_shortest_paths(self, g, src, dst, k=8):
        return yens.k_shortest_paths(g, src, dst, k)[1]

    def ecmp_paths(self, g, src, dst, k=8):
        paths = list(nx.all_shortest_paths(g, src, dst))
        if len(paths) > k: paths = paths[:k]
        return paths

    # Creates routing table:
    # switch_id -> (node_id -> [egress ports])
    def generate_dports(self, topo, path_fn):
        rtable = defaultdict(lambda: dict())

        # create map from node name -> (node name -> egress port)
        links = topo.links(withInfo=True)
        port_map = defaultdict(lambda: dict())
        for l in links:
            port_map[l[0]][l[1]] = l[2]['port1']
            port_map[l[1]][l[0]] = l[2]['port2']

        switches = self.topo.switches()
        g = nx.Graph()
        g.add_nodes_from(self.topo.nodes())
        g.add_edges_from(self.topo.links())

        # find paths from each switch to each node
        for src in switches:
            for dst in filter(lambda n: n != src, topo.nodes()):
                paths = self.path_fn(g, src, dst)
                # convert paths to egress ports
                rtable[src][dst] = [port_map[src][p[1]] for p in paths]

        return rtable

    # generates paths for random permutation traffic
    # (each host connected to only one other host)
    def generate_random_permutation_paths(self):
        all_paths = []

        hosts = self.topo.hosts()
        g = nx.Graph()
        g.add_nodes_from(self.topo.nodes())
        g.add_edges_from(self.topo.links())

        # find paths between pairs of nodes (that have paths)
        pairs = itertools.combinations(hosts, 2)
        pairs = filter(lambda p: nx.has_path(g, *p), pairs)

        while pairs:
            src, dst = random.choice(pairs)
            # remove all pairs connected to nodes that already have paths
            pairs = filter(lambda p: src not in p and dst not in p, pairs)
            paths = self.path_fn(g, src, dst)
            all_paths.extend(paths)

        return all_paths

    # returns a map from link to the number of distinct paths that link is on
    def edge_counts(self, paths):
        edge_counts = { tuple(sorted(e)): 0 for e in self.topo.links() }
        for p in paths:
            edges = [tuple(sorted([p[i], p[i+1]])) for i in range(len(p) - 1)]
            for e in edges:
                edge_counts[e] += 1
        return edge_counts

    def get_egress_port(self, packet, switch_dpid):
        return of.OFPP_FLOOD
        pass # TODO: implement.

    def register_switch(self, switch):
        """
        This is called whenever a new switch comes up in a topology.

        TODO: set whatever internal Routing state is needed.
        """
        pass
