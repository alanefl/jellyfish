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
This component is for use with the OpenFlow tutorial.

It implements the ECMP routing algorithm.

  Resources for algorithm:
    - https://ieeexplore.ieee.org/document/6848095/
    - https://tools.ietf.org/html/rfc2992
    - https://www.quora.com/How-does-ECMP-equal-cost-multi-path-routing-work

n-way ECMP works, roughly, by:
  1) Statically calculating all the shortest paths from
  2) Hashing each incoming packet equally along each of these top n paths

"""

from pox.core import core
from pox.lib.util import dpidToStr
from utils import build_topology, build_routing
from pox.lib.revent import EventMixin
import pox.openflow.libopenflow_01 as of

log = core.getLogger()

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

    # Make this controller listen to all openflow events
    self.listenTo(core.openflow, priority=0)


  def send_packet (self, packet_in, out_port):
    """
    Instructs the switch to resend a packet that it had sent to us.
    "packet_in" is the ofp_packet_in object the switch had sent to the
    controller due to a table-miss.
    """
    msg = of.ofp_packet_out()
    msg.data = packet_in

    # Add an action to send to the specified port
    action = of.ofp_action_output(port = out_port)
    msg.actions.append(action)

    # Send message to switch
    self.connection.send(msg)


  def act_like_hub (self, packet, packet_in):
    """
    Implement hub-like behavior -- send all packets to all ports besides
    the input port.
    """
    # We want to output to all ports -- we do that using the special
    # OFPP_ALL port as the output port.  (We could have also used
    # OFPP_FLOOD.)
    self.send_packet(packet_in, of.OFPP_ALL)

    # Note that if we didn't get a valid buffer_id, a slightly better
    # implementation would check that we got the full data before
    # sending it (len(packet_in.data) should be == packet_in.total_len)).


  def forward_packet (self, packet, packet_in):
    """
    Implement switch-like behavior.
    """

    # Here's some psuedocode to start you off implementing a learning
    # switch.  You'll need to rewrite it as real Python code.

    # Learn the port for the source MAC
    self.mac_to_port[packet.src] = packet_in.in_port

    if packet.dst in self.mac_to_port:
      out_port = self.mac_to_port[packet.dst]
    else:
      out_port = of.OFPP_ALL

    if out_port != of.OFPP_ALL:

      log.info("Sending out packet to port")
      # Send packet out the associated port
      self.send_packet(packet_in, out_port)

      # Once you have the above working, try pushing a flow entry
      # instead of resending the packet (comment out the above and
      # uncomment and complete the below.)

      #log.debug("Installing flow...")
      #self.send_packet(packet, out_port)


    else:

      log.info("Flooding packet out")
      # Flood the packet out everything but the input port
      # This part looks familiar, right?
      self.send_packet(packet_in, out_port)

  def _handle_ConnectionUp (self, event):
    """
    Is called whenever a switch in the Mininet topoplogy comes up,
    and registers it in the controller.
    """
    switch_dpid = event.dpid
    switch = self.switches.get(event.dpid)

    # The name of the switch as known by the topology object.
    name_str = "s%d" % switch_dpid

    # Controller ignores switch if this is not a switch we recognize.
    if name_str not in self.t.switches():
      log.warn("Ignoring unknown switch %s" % sw_str)
      return

    # We expect the switch to be None, so we create it.
    if switch is None:
      log.info("Added fresh switch %s" % name_str)
      switch = Switch()
      self.switches[event.dpid] = switch
      switch.connect(event.connection) # Connect the switch to this event.

    else:
      log.warn("Odd - already saw switch %s come up" % sw_str)
      exit(0)

    if len(self.switches) == len(self.t.switches()):
      log.info("Woo!  All switches up")
      self.all_switches_up = True
      if self.mode == 'proactive':
        self._install_proactive_flows()
      if self.mode == 'hybrid':
        self._install_hybrid_static_flows()

  def _handle_PacketIn (self, event):
    """
    Handles packet in messages from the switch.
    """
    switch_dpid = event.dpid

    # TODO: we need to take an action based on the switch this event
    #       was encountered in.

    # TODO: we need to use the global routing object to decide what
    #       egress port to route this thing out of.

    packet = event.parsed # This is the parsed packet data.
    if not packet.parsed:
      log.warning("Ignoring incomplete packet.")
      return

    packet_in = event.ofp # The actual ofp_packet_in message.
    self.forward_packet(packet, packet_in)



def launch (topo=None, routing=None):
  """
  Starts the Controller:

      - topo is a string with comma-separated arguments specifying what
        topology to build.
          e.g.: 'jellyfish,4' 'dummy'

      - routing is a string indicating what routing mechanism to use:
          e.g.: 'ecmp', 'k-shortest-paths'
  """
  log.info("Launching controller")
  if not topo or not routing:
    raise Exception("Topology and Routing mechanism must be specified.")

  my_topology = build_topology(topo)
  my_routing = build_routing(routing, my_topology)
  core.registerNew(JellyfishController, my_topology, my_routing)
