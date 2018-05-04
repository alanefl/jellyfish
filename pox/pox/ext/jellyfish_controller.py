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
sys.path.append("../../")
from pox.core import core
from pox.lib.util import dpidToStr
from utils import build_topology, dpid_to_str
from pox.lib.revent import EventMixin
import pox.openflow.libopenflow_01 as of
from routing import Routing
from switch import Switch

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

    # Make this controller listen to openflow events, like when switches come up
    # or when a packet comes into a switch.
    self.listenTo(core.openflow, priority=0)

  def forward(self, packet, switch, egress_port):
    """
    Forward a packet along the given egress port of
    the given switch.
    """
    log.info("Sending packet out of port %d from switch %d" % (egress_port, switch.dpid))
    switch.send_packet_data(egress_port, packet)

  def _handle_ConnectionUp (self, event):
    """
    Is called whenever a switch in the Mininet topoplogy comes up,
    and registers it in the controller.
    """
    log.info('Connection up')

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
      log.warn("Odd - already saw switch %s come up" % sw_str)
      exit(0)

    if len(self.switches) == len(self.topology.switches()):
      log.info(" Woo!  All switches up")

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

    # What port should we send this packet out from?
    log.info('Getting egress port')
    egress_port = self.routing.get_egress_port(packet, switch_dpid)
    switch = self.switches.get(switch_dpid)

    if switch is None:
        log.warning("Saw an event for a switch that hasn't come up. Ignoring.")
        return

    # Send packet along
    self.forward(packet, switch, egress_port)

# TODO: how to get host information from the mininet topology.

def launch (topo=None, routing=None):
  """
  Starts the Controller:

      - topo is a string with comma-separated arguments specifying what
        topology to build.
          e.g.: 'jellyfish,4' 'dummy'

      - routing is a string indicating what routing mechanism to use:
          e.g.: 'ecmp', 'kshort'
  """
  log.info("Launching controller")
  if not topo or not routing:
    raise Exception("Topology and Routing mechanism must be specified.")

  my_topology = build_topology(topo)
  my_routing = Routing(my_topology, routing, log)
  my_routing.generate_rtable()
  log.info("Launching routing")
  core.registerNew(JellyfishController, my_topology, my_routing)

# for debugging
if __name__ == '__main__':
  topo = 'dummy'
  routing = 'ecmp'
  my_topology = build_topology(topo)
  my_routing = Routing(my_topology, routing, log)
  my_routing.generate_rtable()
