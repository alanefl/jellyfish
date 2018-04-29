# Routing logic.  T

from collections import defaultdict
import pox.openflow.libopenflow_01 as of
import networkx as nx

class Routing():
    """
    The routing object lives inside a Controller and is in charge of
    returning what egress port a packet should exit from some switch.
    """
    def __init__(self, topo, rproto):
        path_fn = None

        if rproto == 'kshort':
            path_fn = self.k_shortest_paths
        elif rproto == 'ecmp':
            path_fn = self.ecmp_paths

        if not path_fn: raise Exception('Unknown routing protocol')

        self.rtable = self.generate_dports(topo, path_fn)

    def k_shortest_paths(self, g, src, dst):
        paths = list(nx.all_simple_paths(g, src, dst))
        return sorted(paths, key=lambda p: len(p))

    def ecmp_paths(self, g, src, dst):
        return list(nx.all_shortest_paths(g, src, dst))

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

        switches = topo.switches()
        g = nx.Graph()
        g.add_nodes_from(topo.nodes())
        g.add_edges_from(topo.links())

        # find paths from each switch to each node
        for src in switches:
            for dst in filter(lambda n: n != src, topo.nodes()):
                paths = path_fn(g, src, dst)
                # all protos use 8 as max paths for now
                if len(paths) > 8: paths = paths[:8]
                # convert paths to egress ports
                rtable[src][dst] = [port_map[src][p[1]] for p in paths]

        return rtable

    def get_egress_port(self, packet, switch_dpid):
        return of.OFPP_FLOOD
        pass # TODO: implement.

    def register_switch(self, switch):
        """
        This is called whenever a new switch comes up in a topology.

        TODO: set whatever internal Routing state is needed.
        """
        pass
