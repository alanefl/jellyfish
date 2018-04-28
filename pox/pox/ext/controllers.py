from mininet.node import Controller
import os

POXDIR = os.getcwd() + '/../..'

# TODO: this file can do with less code replication
class StarterController( Controller ):
    def __init__( self, name, cdir=POXDIR,
                  command='python pox.py',
                  cargs=('log --file=starter.log,w openflow.of_01 --port=%s ext.starter_controller' ),
                  **kwargs ):
        Controller.__init__( self, name, cdir=cdir,
                             command=command,
                             cargs=cargs, **kwargs )

class YensKShortestController( Controller ):
    def __init__( self, name, cdir=POXDIR,
                  command='python pox.py',
                  cargs=('log --file=yens.log,w openflow.of_01 --port=%s ext.yens_kshortest_controller' ),
                  **kwargs ):
        Controller.__init__( self, name, cdir=cdir,
                             command=command,
                             cargs=cargs, **kwargs )

class ECMPController( Controller ):
    def __init__( self, name, cdir=POXDIR,
                  command='python pox.py',
                  cargs=('log --file=ecmp.log,w openflow.of_01 --port=%s ext.ecmp_controller' ),
                  **kwargs ):
        Controller.__init__( self, name, cdir=cdir,
                             command=command,
                             cargs=cargs, **kwargs )

class JellyfishController( Controller ):
    def __init__( self, name, cdir=POXDIR,
                  command='python pox.py',
                  cargs=('log --file=jelly.log,w openflow.of_01 --port=%s ext.jellyfish_controller --topo=dummy,0 --routing=ecmp' ),
                  **kwargs ):
          # TODO: how to propagate the topology/routing to the cmd above
        Controller.__init__( self, name, cdir=cdir,
                             command=command,
                             cargs=cargs, **kwargs )

controllers={ 'starter': StarterController,
              'kshort': YensKShortestController,
              'ecmp': ECMPController,
              'jellyfish': JellyfishController
}
