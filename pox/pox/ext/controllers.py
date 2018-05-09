from mininet.node import Controller
import os

POXDIR = os.getcwd() + '/../..'

class JellyfishController( Controller ):
    def __init__( self, name, cdir=POXDIR,
                  command='python pox.py',
                  cargs=None,
                  **kwargs ):
        cargs = ("log --file=jelly.log,w log.level openflow.of_01 --port=%s "
                  "ext.jellyfish_controller" )
        Controller.__init__( self, name, cdir=cdir,
                             command=command,
                             cargs=cargs, **kwargs )
