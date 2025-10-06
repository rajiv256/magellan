import os

from src.nupack import utils as nutils
from nupack import *


def get_data_dir():
    data_dir = str(__file__).split('/')[-1].replace(".py", "")
    assert os.path.exists(
        f'./data/{data_dir}'), "Place the domains/strands/complexes in data/<file_name>"
    assert os.path.exists(f'./data/{data_dir}/domains.csv')
    assert os.path.exists(f'./data/{data_dir}/strands.csv')
    assert os.path.exists(f'./data/{data_dir}/complexes.csv')
    return data_dir


domains_df, strands_df, complexes_df = nutils.read_data_dir(get_data_dir())
print(domains_df)
domains = nutils.build_domains_from_df(domains_df)
strands = nutils.build_target_strands_from_df(strands_df, domains)
complexes = nutils.build_target_complexes_from_df(complexes_df, strands)



# Specify the hard constraints.
div1 = Diversity(word=4, types=2, scope=[nutils.extract_domain_by_name('drep1',
                                                                       domains),
                                         nutils.extract_domain_by_name('drep2',
                                                                       domains)])
div2 = Diversity(word=6, types=3, scope=[nutils.extract_domain_by_name('drep1',
                                                                       domains),
                                         nutils.extract_domain_by_name('drep2',
                                                                       domains)])
div3 = Diversity(word=10, types=4, scope=[nutils.extract_domain_by_name('drep1',
                                                                        domains),
                                          nutils.extract_domain_by_name('drep2',
                                                                        domains)])
# g4 = Pattern(["G4"], scope=[nutils.extract_strand_by_name('rep1_base',
#                                                           strands),
#                             nutils.extract_strand_by_name('rep2_base',
#                                                           strands)])
# a_t_4 = Pattern(["N4"], scope=[nutils.extract_domain_by_name('drep1',
#                                                              domains),
#                                nutils.extract_domain_by_name('drep2',
#                                                              domains)])
# a_t_3 = Pattern(["W3"], scope=[nutils.extract_domain_by_name('dx',
#                                                              domains),
#                                nutils.extract_domain_by_name('dx1m',
#                                                              domains),
#                                nutils.extract_domain_by_name('dx2m',
#                                                              domains)])


# Specify the soft constraints.
ssm1 = SSM(word=4, weight=0.3)
ssm2 = SSM(word=5, weight=0.4)
ssm3 = SSM(word=6, weight=0.5)

# diff1 = EnergyMatch([
#     nutils.extract_domain_by_name('dx', domains),
#     nutils.extract_domain_by_name('dx1m', domains),
#     nutils.extract_domain_by_name('dx2m', domains)
# ])

# diff2 = EnergyMatch([
#     nutils.extract_domain_by_name('dy1', domains),
#     nutils.extract_domain_by_name('dy2', domains),
#     nutils.extract_domain_by_name('dw', domains)
# ])

BASE_CONC = 1e-7  # 100 nM
concentrations = {}
for c in complexes:
    concentrations[c] = BASE_CONC

base1 = nutils.extract_strand_by_name('base1', strands)
base2 = nutils.extract_strand_by_name('base2', strands)
base3 = nutils.extract_strand_by_name('base3', strands)
sx = nutils.extract_strand_by_name('x', strands)
sx1m = nutils.extract_strand_by_name('x1m', strands)
sx2m = nutils.extract_strand_by_name('x2m', strands)
sy1 = nutils.extract_strand_by_name('y1', strands)
sy2 = nutils.extract_strand_by_name('y2', strands)
sw = nutils.extract_strand_by_name('w', strands)
rep1_base = nutils.extract_strand_by_name('rep1_base', strands)
rep2_base = nutils.extract_strand_by_name('rep2_base', strands)
rep1_out = nutils.extract_strand_by_name('rep1_out', strands)
rep2_out = nutils.extract_strand_by_name('rep2_out', strands)

t1 = TargetTube(on_targets=concentrations, name='t1',
                off_targets=SetSpec(max_size=3, exclude=[[rep1_base,sy1,
                                                          rep1_out],
                                                         [rep2_base,sy2,
                                                          rep2_out]]))

my_options = DesignOptions(f_stop=0.01, seed=93)

model = Model(material='dna', celsius=37, sodium=0.5, magnesium=0.1)

my_design = tube_design(tubes=[t1], model=model, options=my_options,
                        hard_constraints=[div1, div2, div3],
                        soft_constraints=[ssm1, ssm2, ssm3])

results = my_design.run(trials=3)[0]

print(results)

strand_results = list(results.to_analysis.strands.values())
keys = list(results.to_analysis.strands.keys())

data = {}
for strand_result in strand_results:
    data[strand_result] = 1e-7

an1 = Tube(strands=data, complexes=SetSpec(max_size=2), name='an1')

tube_results = tube_analysis(tubes=[an1], model=model)

print(tube_results)

domain_results = results.to_analysis.domains

for k, v in domain_results.items():
    print(k.name, v)

strand_results = results.to_analysis.strands
for k, v in strand_results.items():
    print(k.name, v)