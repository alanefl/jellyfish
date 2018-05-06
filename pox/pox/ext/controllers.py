from mininet.node import Controller
import os

POXDIR = os.getcwd() + '/../..'

class JellyfishController( Controller ):
    def __init__( self, name, cdir=POXDIR,
                  command='python pox.py',
                  cargs=('log --file=jelly.log,w openflow.of_01 --port=%s ext.jellyfish_controller --topo=dummy,0 --routing=kshort' ),
                  **kwargs ):
          # TODO: how to propagate the topology/routing to the cmd above
        Controller.__init__( self, name, cdir=cdir,
                             command=command,
                             cargs=cargs, **kwargs )
