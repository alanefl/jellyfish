# Copyright 2012 James McCauley
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at:
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
JellyfishController class.
"""

import sys
import os
sys.path.append("../../")
from pox.core import core
from pox.lib.util import dpidToStr
from utils import build_topology, dpid_to_str
from pox.lib.revent import EventMixin
import pox.openflow.libopenflow_01 as of
from routing import Routing
from switch import Switch
from pox.lib.packet import ipv4, tcp, udp
from topologies import topologies

class FakeLogger():
  def info(self, txt):
    print(txt)

log = core.getLogger() if core else FakeLogger()

class JellyfishController (EventMixin):
  """
  An JellyfishController object is created once, and it is in charge of instantiating
  all of the switches in the Controller as they come up in the mininet topology.

  A JellyfishController subclasses EventMixin, because it is triggered when
  certain events happen in the mininet network.

  The Jellyfish Controller consumes ALL packet_in events and demultiplexes
  them to the correct switch and switch action, after determining what
  action must occur using an internal routing class.
  """
  def __init__ (self, topology, routing):
    # Keep track of the connection to the switch so that we can
    # send it messages!
    self.routing = routing
    self.switches = {}  # Switches seen: [dpid] -> Switch
    self.topology = topology  # Master Topo object, passed in and never modified.
    self.routing = routing  # Master Routing object, passed in and reused.
    self.all_switches_up = False  # Sequences event handling.
    self.switch_dst_eth_seen = [] # Keeps track of what (switch, dst_eth) pairs we've seen

    # Make this controller listen to openflow events, like when switches come up
    # or when a packet comes into a switch.
    self.listenTo(core.openflow, priority=0)

  def forward(self, connection, packet, switch, egress_port):
    """
    Forward a packet along the given egress port of
    the given switch.

    Forwarding actually only happens the first time, because the first time
    we install a flow rule in the switch so that we don't have to get repeated
    requests for an egress port.
    """

   # if (switch, packet.dst) in self.switch_dst_eth_seen:
      # This should not happen
    #  log.warn("Saw packet heading to to the same place on same switch again :(")

    log.info("Sending packet out of port %d from switch %d" % (egress_port, switch.dpid))

    # 1) Tell the switch to always send these packets with these
    #    hash properties from this port

    msg = of.ofp_flow_mod()
    msg.match.dl_dst = packet.dst
    msg.match.dl_src = packet.src
    msg.match.dl_type = packet.type
    if isinstance(packet.next, ipv4):
      ip = packet.next
      msg.match.nw_proto = ip.protocol
      msg.match.nw_dst = ip.dstip.toUnsigned()
      msg.match.nw_src = ip.srcip.toUnsigned()
      if isinstance(ip.next, tcp) or isinstance(ip.next, udp):
        l4 = ip.next
        msg.match.tp_src = l4.srcport
        msg.match.tp_dst = l4.dstport
    msg.actions.append(of.ofp_action_output(port = egress_port))
    connection.send(msg)

    #self.switch_dst_eth_seen.append((switch, packet.dst))

    # 2) But send we have to send this packet out ourselves..
    switch.send_packet_data(egress_port, packet)

  def _handle_ConnectionUp (self, event):
    """
    Is called whenever a switch in the Mininet topoplogy comes up,
    and registers it in the controller.
    """
    log.info('Connection up')
    log.info(event.connection.features)
    log.info(event.ofp)
    switch_dpid = event.dpid
    switch = self.switches.get(event.dpid)

    # The name of the switch as known by the topology object.
    switch_name_str = dpid_to_str(switch_dpid)

    # Controller ignores switch if this is not a switch we recognize.
    if switch_name_str not in self.topology.switches():
      log.warn("Ignoring unknown switch %s" % switch_name_str)
      return

    # We expect the switch to be None, so we create it.
    if switch is None:
      log.info("Added fresh switch %s" % switch_name_str)
      switch = Switch(log)
      self.switches[event.dpid] = switch
      switch.connect(event.connection) # Connect the switch to this event.

      # Give the Routing class the new switch object for registration.
      self.routing.register_switch(switch)

    else:
      log.warn("Odd - already saw switch %s come up" % switch_name_str)

    if len(self.switches) == len(self.topology.switches()):
      log.info(" Woo!  All switches up")

    # Not sure if this is necessary: Clear all flow table entries for this switch
    # But does not affect ping all success.
    clear = of.ofp_flow_mod(command=of.OFPFC_DELETE)
    event.connection.send(clear)
    event.connection.send(of.ofp_barrier_request())


  def _handle_ConnectionDown (self, event):
    self.switches.get(event.dpid).disconnect()

  def _handle_PacketIn (self, event):
    """
    Handles packet in messages for all switches.

    Takes a packet and routes it out of the correct switch on the
    correct egress port.
    """

    # What switch are we talking about here?
    switch_dpid = event.dpid


    # Get packet data
    packet = event.parsed
    if not packet.parsed:
      log.warning("Ignoring incomplete packet.")
      return

    if str(packet.dst) == "ff:ff:ff:ff:ff:ff":
      # We should not be dealing with any broadcast packets.
      # These are usually DHCP, we can ignore since we have knowledge
      # of all topology addressing.
      return

    # What port should we send this packet out from?

    # Uncomment stuff below to dump lots of info about the packet we
    # just received

    """
    log.info("Event raised on eth address:  " + str(event.connection.eth_addr))
    log.info('Getting egress port for this packet on switch %d:' % switch_dpid)
    log.info((packet.src, packet.dst))
    log.info(packet.dump())
    log.info(packet.effective_ethertype)

    """

    egress_port = self.routing.get_egress_port(packet, switch_dpid)
    switch = self.switches.get(switch_dpid)

    if switch is None:
        log.warning("Saw an event for a switch that hasn't come up. Ignoring.")
        return

    # Send packet along
    self.forward(event.connection, packet, switch, egress_port)

def launch ():
  """
  Starts the Controller:

      - topo is a string with comma-separated arguments specifying what
        topology to build.
          e.g.: 'jellyfish,4'

      - routing is a string indicating what routing mechanism to use:
          e.g.: 'ecmp8', 'kshort'
  """

  # NOTE: currently only support jellyfish topology.

  log.info("Launching Jellyfish controller")
  # Read out configuration from file.

  # NOTE: assumes jellyfish has been installed in the home directory.
  config_loc = os.environ['HOME'] + '/jellyfish/pox/pox/ext/__jellyconfig'
  with open(config_loc, 'r', os.O_NONBLOCK) as config_file:
    log.info("inside")
    n = int(config_file.readline().split('=')[1])
    k = int(config_file.readline().split('=')[1])
    r = int(config_file.readline().split('=')[1])
    seed = int(config_file.readline().split('=')[1])
    routing = config_file.readline().split('=')[1].strip()

  jelly_topology = topologies["jelly"](random_seed=seed, n=n, k=k, r=r)
  my_routing = Routing(jelly_topology, routing, log, seed=seed)
  my_routing.generate_rtable()
  core.registerNew(JellyfishController, jelly_topology, my_routing)


# for debugging
if __name__ == '__main__':
  topo = 'dummy'
  routing = 'ecmp'
  my_topology = build_topology(topo)
  my_routing = Routing(my_topology, routing, log)
  my_routing.generate_rtable()
