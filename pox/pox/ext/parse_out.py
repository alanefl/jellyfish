#
# Takes the output file from a test run and displays it nicely.
#

percentages = []
with open('test_out', 'r') as out:
    for line in out:
      if line.startswith('Percentage of NIC rate:'):
        percentages.append(line.split()[-1])

experiment_order = ['TCP 1 Flow  w/   8ECMP',
                    'TCP 8 Flows w/   8ECMP',
                    'TCP 1 Flow  w/ 8KSHORT',
                    'TCP 8 Flows w/ 8KSHORT']

print("\n\n ~~ Final Results: Table 1 ~~\n")
for idx, p in enumerate(percentages):
  print("    %s --> %s" % (experiment_order[idx], p))