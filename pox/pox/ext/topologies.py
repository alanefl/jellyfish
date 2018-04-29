
import itertools
import random
from mininet.topo import Topo

"""
Keep all topology definitions for PA2 in this file.

"""

NUM_PORTS = 3

class JellyfishTopo(Topo):
    """
    Creates a topology with n switches, each of which has k ports,
    r of which are connected to other switches.
    They are connected to each other using the jellyfish algorithm
    """
    def build(self, n=4, k=NUM_PORTS, r=2, random_seed=0):

        r = k - 1 if r is None else r

        # For reproducing the topology in the controller and in the
        # Mininet instance.
        random.seed(random_seed)

        self.switch_ports_remaining = dict()
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

        # run jellyfish to connect switches to one another
        self.make_jellyfish_topo()

        # since there is not actual removeLink method, only add links at the end
        for l in self.temp_links: self.addLink(*l)

    def make_jellyfish_topo(self):
        # while possible, join two random switches with free ports
        while True:
            p = self.next_pair()
            if not p:
                break
            self.temp_links.append(p)
            self.switch_ports_remaining[p[0]] -= 1
            self.switch_ports_remaining[p[1]] -= 1

        # if a switch remains with >=2 free ports (p1, p2),
        # pick a random existing link (x, y), remove it,
        # and connect (p1, x) and (p2, y)
        remain = filter(lambda s: self.switch_ports_remaining[s] >= 2, self.switches())
        if remain:
            s = remain[0]
            neighbors = filter(lambda l: s in l, self.temp_links)
            neighbors = [filter(lambda l: l != s, l)[0] for l in neighbors]
            possible = filter(lambda l: s not in l and l[0] not in neighbors \
                and l[1] not in neighbors, self.temp_links)
            if possible:
                l = possible[0]
                self.temp_links.remove(l)
                self.temp_links.append((s, l[0]))
                self.temp_links.append((s, l[1]))

    def next_pair(self):
        """
        Get the next random switch pair to connect.
        """
        avail = filter(lambda s: self.switch_ports_remaining[s] > 0, self.switches())
        pairs = itertools.combinations(avail, 2)
        pairs = filter(lambda p: p not in self.temp_links, pairs)
        random.shuffle(pairs)
        return None if len(pairs) == 0 else pairs[0]

class DummyTopo(Topo):
    """
    Creates a very simple topology:

            hx -- sy -- hz

    Used to test that the ECMP/k-shortest-paths controllers
    are working fine.
    """

    def build(self, random_seed=0):

        random.seed(random_seed)
        x = random.randint(0, 9)

        # Add hosts and switches.
        #   Add some randomness to exercise the random seed functionality
        #   (we want exact same topology to be built for the mininet instance
        #   as for the controller class)

        leftHost = self.addHost('h%d' % x)
        rightHost = self.addHost('h%d' % (x + 1))
        switch = self.addSwitch('s%d' % (x + 2))

        # Add links
        self.addLink(leftHost, switch)
        self.addLink(switch, rightHost)

        return

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
