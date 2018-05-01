from mininet.topo import Topo
from collections import defaultdict
import random

"""
Keep all topology definitions for PA2 in this file.

"""

NUM_PORTS = 3

class JellyfishTopo(Topo):
    """
    Creates a topology with n switches, each of which has k ports,
    r of which are connected to other switches
    They are connected to each other using the jellyfish algorithm
    """
    def build(self, n=4, k=NUM_PORTS, r=None):
        if r is None: r = k-1
        self.switch_ports_remaining = dict()
        self.remaining_switches = [] # switches that have >1 port left
        self.connections = defaultdict(lambda: []) # switch -> list of connected switches
        self.temp_links = []

        # add n switches, each attached to k hosts
        for i in range(n):
            s = self.addSwitch('s{}'.format(i))
            for j in range(k-r):
                h = self.addHost('h{}_{}'.format(i, j))
                self.addLink(h, s)
            # Note: to actually add the ports to the switch, we could use
            #       map(s.attach, range(NUM_PORTS))
            #       however, switch numbers don't matter, only the number of
            #       remaining switches, so this seemed simpler.
            self.switch_ports_remaining[s] = r
            self.remaining_switches.append(s)

        # run jellyfish to connect switches to one another
        self.make_jellyfish_topo()

        # since there is not actual removeLink method, only add links at the end
        for l in self.temp_links: self.addLink(*l)

    def make_jellyfish_topo(self):
        # while possible, join two random switches with free ports
        while True:
            p = self.find_available_pair()
            if not p: break
            self.temp_links.append(p)
            self.connections[p[0]].append(p[1])
            self.connections[p[1]].append(p[0])
            for s in p:
                self.switch_ports_remaining[s] -= 1
                if self.switch_ports_remaining[s] == 0:
                    self.remaining_switches.remove(s)

        # if a switch remains with >=2 free ports (p1, p2),
        # pick a random existing link (x, y), remove it,
        # and connect (p1, x) and (p2, y)
        if self.remaining_switches:
            s = self.remaining_switches[0]
            connected = self.connections[s]
            # the switch must already be connected to neither switch
            possible = filter(lambda l: l[0] not in connected and l[1] not in connected,
                self.temp_links)
            if possible:
                l = possible[0]
                self.temp_links.remove(l)
                self.temp_links.append((s, l[0]))
                self.temp_links.append((s, l[1]))

    def find_available_pair(self):
        random.shuffle(self.remaining_switches) # this is slow, but necessary...
        for s1 in self.remaining_switches:
            for s2 in self.remaining_switches:
                if s1 == s2: continue
                if s2 in self.connections[s1]: continue
                return (s1, s2)
        return None

    def generate_rtable(self):
        """
        TODO: figure out the proper way to do custom routing in mininet...
        may there will be open source implementations!
        This may be helpful for implementing k shortest path routing:
        http://thinkingscale.com/k-shortest-paths-cpp-version/
        """
        pass

class DummyTopo(Topo):
    """
    Creates a very simple topology:

            h0 -- s0 -- h1

    Used to test that the ECMP/k-shortest-paths controllers
    are working fine.
    """

    def build(self):

        # Add hosts and switches
        leftHost = self.addHost( 'h0' )
        rightHost = self.addHost( 's0' )
        switch = self.addSwitch( 'h1' )

        # Add links
        self.addLink( leftHost, switch )
        self.addLink( switch, rightHost )


class FatTreeTopo(Topo):
    """
    TODO: implement!
    Is it possible to use subclass the tree topology here?
    https://github.com/mininet/mininet/blob/master/mininet/topolib.py
    """
    pass

topologies = {'ft': FatTreeTopo, 'jelly': JellyfishTopo, 'dummy': DummyTopo}

from routing import Routing

if __name__ == '__main__':
    # Create Jellyfish Topology
    topo = JellyfishTopo()
    routing = Routing(topo, 'kshort')
    for i in routing.rtable.items(): print(i)
