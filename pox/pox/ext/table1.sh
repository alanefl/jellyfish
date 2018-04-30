#
# Runs the experiments to generate Table 1 on Jellyfish paper.
#

# NOTE: I am assuming a NIC output rate of 10 GBps
#       based on the command:
#         mininet> dpctl dump-ports-desc

#
# NOTE: my current plan is to run IPERF client and servers and
#       all machine pairs, and use that to measure throughput.
#
#       I need to set up iperf servers on the targets, and iperf
#       clients on the sending hosts.  I can use the -P flag
#       to tell a host how many flows to send in parallel.
#
#    TODO: can we use monitor functions from mininet to do this easily?
#

# NOTE: assumes TCP default congestion control is cubic or reno.

echo '**** Running test: random permutation traffic, 1 TCP flow ****'
# 1. Run random permutation traffic test on Jellyfish topology with
#    780 servers. With congestion control: TCP 1 flow
#
#    TODO: actually support this with jellyfish.  This is a placeholder.
sudo sysctl -w net.mptcp.mptcp_enabled=0 # Turn off MPTCP
sudo python run.py -randpermtraffic --flows 1 -t dummy


exit

echo '**** Running test: random permutation traffic, 8 TCP flows ****'
# 2. Run random permutation traffic test on Jellyfish topology with
#    780 servers. With congestion control: TCP 8 flows
#    TODO: actually support this with jellyfish.  This is a placeholder.
sudo python run.py -randpermtraffic --flows 8 -t dummy

# NOTE: Using MPTCP as described here:
#    - https://multipath-tcp.org/pmwiki.php/Users/AptRepository
#
#      Reference for getting MPTCP to work: https://github.com/bocon13/mptcp_setup
#
# 3. Run random permutation traffic test on Jellyfish topology with
#    780 servers. With congestion control: MPTCP 8 subflows
#
#    TODO: actually support this with jellyfish.  This is a placeholder.
sudo sysctl -w net.mptcp.mptcp_enabled=1 # Turn on MPTCP
sudo python run.py -randpermtraffic --flows 8 -t dummy
sudo sysctl -w net.mptcp.mptcp_enabled=0 # Turn off MPTCP again