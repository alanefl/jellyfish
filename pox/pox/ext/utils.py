# Utility functions

from topologies import topologies

def build_topology(topo):
    """
    Topo is a string indicating what topology to build,
    and perhaps some arguments.

        e.g. dummy,arg1,arg2
    """
    topo_split = topo.split(',')
    topo_name = topo_split[0]     # e.g. dummy
    topo_params = topo_split[1:]  # e.g. [arg1, arg2]

    # Convert int and float args; removes the need for every topology to
    # be flexible with input arg formats.
    topo_seq_params = [ s for s in topo_params if '=' not in s ]
    topo_seq_params = [ int(s) for s in topo_seq_params ]
    topo_kw_params = {}
    for s in [ p for p in topo_params if '=' in p ]:
        key, val = s.split( '=' )
        topo_kw_params[key] = int(val)

    if topo_name not in topologies.keys():
        raise Exception( 'Invalid topo_name %s' % topo_name )
    return topologies[topo_name](*topo_seq_params, **topo_kw_params)

def dpid_to_str(dpid):
    return "s%d" % dpid