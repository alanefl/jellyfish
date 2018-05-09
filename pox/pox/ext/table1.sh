#
# Runs the experiments to generate a subset of Table 1 on Jellyfish paper.
#


echo '**** Running test: random permutation traffic, 1 TCP flow, ECMP ****'

rm test_out
sudo mn -c

# 1. Run random permutation traffic test on Jellyfish topology with
#    n=25, k=4, r=3. With congestion control: TCP 1 flows, Routing: ECMP
sudo python run.py -randpermtraffic --flows 1 -t jelly,25,4,3 --routing ecmp --seed 0 > test_out


echo '**** Running test: random permutation traffic, 8 TCP flows, ECMP ****'

# 2. Run random permutation traffic test on Jellyfish topology with
#    n=25, k=4, r=3. With congestion control: TCP 8 flows, Routing: ECMP
sudo python run.py -randpermtraffic --flows 8 -t jelly,25,4,3 --routing ecmp --seed 0 > test_out

echo '**** Running test: random permutation traffic, 1 TCP flow, KSHORT ****'

# 3. Run random permutation traffic test on Jellyfish topology with
#    n=10, k=4, r=3. With congestion control: TCP 1 flows, Routing: ECMP
sudo python run.py -randpermtraffic --flows 1 -t jelly,10,4,3 --routing kshort --seed 0 > test_out

echo '**** Running test: random permutation traffic, 8 TCP flows, KSHORT ****'

# 4. Run random permutation traffic test on Jellyfish topology with
#    n=10, k=4, r=3. With congestion control: TCP 8 flows, Routing: ECMP
sudo python run.py -randpermtraffic --flows 8 -t jelly,10,4,3 --routing kshort --seed 0 > test_out

python parse_out.py
rm test_out