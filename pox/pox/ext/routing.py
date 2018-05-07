#!/usr/bin/python

from collections import defaultdict
from functools import partial
import networkx as nx
import itertools
import random

from topologies import dpid_to_mac_addr, node_name_to_dpid, dpid_to_switch
import pox.openflow.libopenflow_01 as of

import yens

class Routing():
    def __init__(self, topo, rproto, log):
        self.topo = topo
        self.log = log

        self.log.info("Setting proto")
        self.set_path_fn(rproto)

        self.hostname_to_mac = {} # Maps hostnames to mac addresses.
        for host in topo.hosts():
            self.hostname_to_mac[host] = dpid_to_mac_addr(node_name_to_dpid(host))
        self.log.info(self.hostname_to_mac)

    def set_path_fn(self, rproto):
        self.path_fn = None

        if rproto == 'kshort': # use 8 as k
            self.path_fn = partial(self.k_shortest_paths, k=8)
        elif rproto == 'ecmp8' or rproto == 'ecmp':
            self.path_fn = partial(self.ecmp_paths, k=8)
        elif rproto == 'ecmp64':
            self.path_fn = partial(self.ecmp_paths, k=64)

        if not self.path_fn: raise Exception('Unknown routing protocol')

    def generate_rtable(self):
        self.generate_routing_paths()

    def k_shortest_paths(self, g, src, dst, k=8):
        return yens.k_shortest_paths(g, src, dst, k)[1]

    def ecmp_paths(self, g, src, dst, k=8):
        paths = list(nx.all_shortest_paths(g, src, dst))
        if len(paths) > k: paths = paths[:k]
        return paths

    # Creates path map:
    # host src eth -> (host src eth -> [possible paths])
    def generate_routing_paths(self):
        self.routing_paths = defaultdict(lambda: dict())

        # create map from node name -> (node name -> egress port)
        links = self.topo.links(withInfo=True)
        self.port_map = defaultdict(lambda: dict())
        for l in links:
            self.port_map[l[0]][l[1]] = l[2]['port1']
            self.port_map[l[1]][l[0]] = l[2]['port2']

        hosts = self.topo.hosts()
        g = nx.Graph()
        g.add_nodes_from(self.topo.nodes())
        g.add_edges_from(self.topo.links())

        # find paths from each host to each host
        # note: we do not know how to route to other switches, only other hosts
        for src in hosts:
            for dst in filter(lambda h: h != src, hosts):
                paths = self.path_fn(g, src, dst)
                # convert paths to egress ports
                src_mac = self.hostname_to_mac[src]
                dst_mac = self.hostname_to_mac[dst]
                self.routing_paths[src_mac][dst_mac] = paths

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

    def _ecmp_hash(self, packet):
        "Return an ECMP-style 5-tuple hash for TCP/IP packets, otherwise 0."
        hash_input = [0] * 5
        if isinstance(packet.next, ipv4):
          ip = packet.next
          hash_input[0] = ip.srcip.toUnsigned()
          hash_input[1] = ip.dstip.toUnsigned()
          hash_input[2] = ip.protocol
          if isinstance(ip.next, tcp) or isinstance(ip.next, udp):
            l4 = ip.next
            hash_input[3] = l4.srcport
            hash_input[4] = l4.dstport
            return crc32(pack('LLHHH', *hash_input))
        return 0

    # get paths between src and dst mac address of packet
    # choose path deterministically based on hash from packet data
    # find current switch in path, and find egress port to get
    # to next hop in the path
    def get_egress_port(self, packet, switch_dpid):

        # This should actually never happen.
        if str(packet.dst) == 'ff:ff:ff:ff:ff:ff':
            self.log.warn('Broadcasting packet..')
            return of.OFPP_FLOOD

        paths = self.routing_paths[str(packet.src)][str(packet.dst)]
        """
        TODO: get proper ECMP hashing working
        index = len(paths) % self._ecmp_hash(packet)
        path = paths[index]
        """
        path = random.choice(paths)

        switch_id = dpid_to_switch(switch_dpid)

        # NOTE: we must choose a path that contains the current
        #       switch.
        while switch_id not in path:
            path = random.choice(paths)

        switch_index = path.index(switch_id)
        return self.port_map[switch_id][path[switch_index + 1]]

    def register_switch(self, switch):
        """
        This is called whenever a new switch comes up in a topology.

        TODO: set whatever internal Routing state is needed.
        """
        pass
