# Switch abstraction for use by the controller

import pox.openflow.libopenflow_01 as of
from pox.lib.revent import EventMixin

class Switch(EventMixin):

  def __init__ (self, logger):
    self.connection = None
    self.ports = None
    self.dpid = None
    self._listeners = None
    self.log = logger

  def disconnect (self):
    if self.connection is not None:
      self.log.debug("Disconnect %s" % (self.connection,))
      self.connection.removeListeners(self._listeners)
      self.connection = None
      self._listeners = None

  def connect (self, connection):
    if self.dpid is None:
      self.dpid = connection.dpid
    if self.ports is None:
      self.ports = connection.features.ports
    self.disconnect()
    self.log.debug("Connect %s" % (connection,))
    self.connection = connection
    self._listeners = self.listenTo(connection)

  def send_packet_data(self, outport, data = None):
    msg = of.ofp_packet_out(in_port=of.OFPP_NONE, data = data)
    msg.actions.append(of.ofp_action_output(port = outport))
    self.connection.send(msg)

  def _handle_ConnectionDown (self, event):
    self.disconnect()
