from mininet.topo import Topo
from collections import defaultdict
import random

"""
Keep all topology definitions for PA2 in this file.

"""

NUM_PORTS = 4
BW = 10

class JellyfishTopo(Topo):
    """
    Creates a topology with n switches, each of which has k ports,
    r of which are connected to other switches.
    They are connected to each other using the jellyfish algorithm
    """
    def build(self, random_seed=0, n=15, k=NUM_PORTS, r=None):
        if r is None: r = k-1

       # n = 8
        # k = 6
        # r = 4

        # For reproducing the topology in the controller and in the
        # Mininet instance.
        random.seed(random_seed)

        self.switch_ports_remaining = dict()
        self.remaining_switches = [] # switches that have >1 port left
        self.connections = defaultdict(lambda: []) # switch -> list of connected switches
        self.temp_links = []

        # add n switches, each attached to k hosts
        # The number x in (s|h)x must be globally unique
        # across the topology.
        #
        # We assign a pid incrementally to every switch or host that comes up.
        pid_ctr = 1
        for i in range(1,n+1): # so that i is not 0
            """
            NOTE: setting the IP of the switch here doesn't seem to do anything,
                  though the IP of the host is set.
            """
            s = self.addSwitch('s{}'.format(pid_ctr))
            pid_ctr += 1
            for j in range(k-r):
                h = self.addHost('h{}'.format(pid_ctr), mac=dpid_to_mac_addr(pid_ctr),
                    ip=dpid_to_ip_addr(pid_ctr))
                self.addLink(h, s, bw=BW)
                pid_ctr += 1
            # Note: to actually add the ports to the switch, we could use
            #       map(s.attach, range(NUM_PORTS))
            #       however, switch numbers don't matter, only the number of
            #       remaining switches, so this seemed simpler.
            self.switch_ports_remaining[s] = r
            self.remaining_switches.append(s)

        # run jellyfish to connect switches to one another
        self.make_jellyfish_topo()

        # since there is not actual removeLink method, only add links at the end
        for l in self.temp_links: self.addLink(*l, bw=BW)

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

        leftHostdpid = x
        rightHostdpid = x + 1
        switchdpid = x + 2


        leftHost = self.addHost('h%d' % leftHostdpid, mac=dpid_to_mac_addr(leftHostdpid))
        rightHost = self.addHost('h%d' % rightHostdpid, mac=dpid_to_mac_addr(rightHostdpid))
        switch = self.addSwitch('s%d' % switchdpid)

        # Add links
        self.addLink(leftHost, switch)
        self.addLink(switch, rightHost)


class FatTreeTopo(Topo):
    """
    TODO: implement!
    Is it possible to use subclass the tree topology here?
    https://github.com/mininet/mininet/blob/master/mininet/topolib.py
    """
    pass

topologies = {'ft': FatTreeTopo, 'jelly': JellyfishTopo, 'dummy': DummyTopo}


# TODO: can't add these to util because of circular imports
def dpid_to_mac_addr(dpid):
    """
    Converts decimal number to string mac address.

    42 ==> "00:00:00:00:00:2a"

    Thanks: https://stackoverflow.com/questions/9020843/how-to-convert-a-mac-number-to-mac-string
            https://stackoverflow.com/questions/12638408/decorating-hex-function-to-pad-zeros
    """
    interm = "{0:0{1}x}".format(dpid,12)
    return ':'.join(s.encode('hex') for s in interm.decode('hex'))

def dpid_to_ip_addr(dpid):
    """
    Returns 10.0.0.<dpid>
    """
    import socket, struct
    addr = socket.inet_ntoa(struct.pack('!L', dpid))
    return "10" + addr[1:]

def node_name_to_dpid(host_name):
    return int(host_name[1:])

def dpid_to_switch(dpid):
    return 's{}'.format(dpid)

if __name__ == '__main__':
    # Create Jellyfish Topology
    topo = JellyfishTopo()
