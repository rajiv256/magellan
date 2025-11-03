#!/usr/bin/env python3

from nupack import *

# Read sequences from sequences.txt
sequences = {}
with open('sequences.txt', 'r') as f:
    for line in f:
        line = line.strip()
        if line:
            name, seq = line.split()
            sequences[name] = seq

# Set up NUPACK model
model = Model(material='dna', celsius=37, sodium=0.05, magnesium=0.01)

# Create strand objects
strands = {}
for name, seq in sequences.items():
    strands[name] = Strand(seq, name=name)

# Set concentrations based on naming convention
concentrations = {}
for name in sequences.keys():
    if name.endswith('bot'):
        concentrations[strands[name]] = 1.0e-6
    elif name.endswith('top'):
        concentrations[strands[name]] = 1.2e-6
    else:
        concentrations[strands[name]] = 1.4e-6

# Create tube with all strands
tube = Tube(strands=concentrations, complexes=SetSpec(max_size=4), name='tube1')

# Run complex analysis
tube_result = tube_analysis(tubes=[tube], model=model, compute=['pfunc','pairs', 'mfe', 'sample'],)

# Print results
print("Complex Analysis Results")
print("=" * 80)
print(f"\nTotal number of complexes: {len(tube_result.complexes)}")
print("\nTop complexes by concentration:")
print("-" * 80)

# Sort complexes by concentration
complex_concs = [(complex, tube_result.complex_concentrations[0][i])
                 for i, complex in enumerate(tube_result.complexes)]
complex_concs.sort(key=lambda x: x[1], reverse=True)

# Print top 20 complexes
for i, (complex, conc) in enumerate(complex_concs[:20], 1):
    print(f"{i}. {complex} : {conc:.3e} M")

# Save full results to file
with open('results.txt', 'w') as f:
    f.write("All Complex Concentrations\n")
    f.write("=" * 80 + "\n\n")
    for complex, conc in complex_concs:
        f.write(f"{complex} : {conc:.3e} M\n")

print("\nFull results saved to results.txt")