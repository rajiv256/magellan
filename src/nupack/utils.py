import re
from typing import List
import itertools
import pandas as pd
from nupack import *


def extract_index_by_name(name: str, l: List[str]) -> int:
    index = -1
    for idx, elem in enumerate(l):
        if elem == name:
            index = idx
            break
    if index == -1:
        print(name, l)
    assert index != -1, "Name not found!"
    return index


def extract_strand_by_name(name: str, strands: List[TargetStrand]):
    names = [strand.name for strand in strands]
    return strands[extract_index_by_name(name, names)]


def extract_domain_by_name(name: str, domains: List[Domain]):
    names = [d.name for d in domains]
    return domains[extract_index_by_name(name, names)]


def extract_complex_by_name(name: str, complexes: List[Complex]):
    names = [c.name for c in complexes]
    return complexes[extract_index_by_name(name, names)]


def read_lines(filepath):
    lines = []
    with open(filepath, 'r') as fin:
        lines = fin.readlines()
        lines = [line.strip() for line in lines]
    return lines


def read_data_dir(data_dir: str, sep: str = '\t') -> [pd.DataFrame] * 3:
    domains_csv = os.path.join('data', data_dir, 'domains.csv')
    domains_df = pd.read_csv(domains_csv, sep=sep)

    strands_csv = os.path.join('data', data_dir, 'strands.csv')
    strands_df = pd.read_csv(strands_csv, sep=sep)

    complexes_csv = os.path.join('data', data_dir, 'complexes.csv')
    complexes_df = pd.read_csv(complexes_csv, sep=sep)

    return domains_df, strands_df, complexes_df


def create_domain(name: str, code: str) -> Domain:
    """code must be acceptable.
    Code	Nucleotides
M	A or C
R	A or G
W	A or U
S	C or G
Y	C or U
K	G or U
V	A, C, or G
H	A, C, or U
D	A, G, or U
B	C, G, or U
N	A, C, G, or U
For DNA, T replaces U.
    """
    assert re.match('([MRWSYKVHDBNATGCU][0-9]+)*', code)
    d = Domain(code, name=name)
    return d


def build_domains_from_df(df) -> List[Domain]:
    domains = [create_domain(name, code) for name, code in
               zip(df.name, df.code)]
    return domains


def create_target_strand(name: str, domains_raw: str, domains: List[Domain],
                         sep=',') -> TargetStrand:
    """code must be acceptable.
    Code	Nucleotides
M	A or C
R	A or G
W	A or U
S	C or G
Y	C or U
K	G or U
V	A, C, or G
H	A, C, or U
D	A, G, or U
B	C, G, or U
N	A, C, G, or U
For DNA, T replaces U.
    """
    strand_domains = []
    all_domains = [d.name for d in domains]
    strand_domains_list = domains_raw.split(sep)

    for domain_str in strand_domains_list:
        revcompFlag = False
        if '~' in domain_str:
            revcompFlag = True
        domain_str = domain_str.replace('~', '')

        # Extract the index of the domain in the total domains list.
        index = extract_index_by_name(domain_str, all_domains)

        if revcompFlag:
            strand_domains.append(~domains[index])
        else:
            strand_domains.append(domains[index])
    s = TargetStrand(strand_domains, name=name)
    return s


def build_target_strands_from_df(df, domains=[]):
    assert len(domains) > 0, "Domains empty!"
    strands = [
        create_target_strand(name, domains_raw, domains)
        for name, domains_raw in zip(df.name, df.domains)
    ]
    return strands


def create_target_complex(name: str, strands_raw: str, code: str,
                          strands: List[TargetStrand],
                          sep=',') -> TargetComplex:
    all_strand_names = [strand.name for strand in strands]
    complex_strand_names = strands_raw.split(sep)
    complex_strands = []

    for sname in complex_strand_names:
        index = extract_index_by_name(sname, all_strand_names)
        complex_strands.append(strands[index])

    complex = TargetComplex(complex_strands, code, name=name)
    return complex


def build_target_complexes_from_df(df, strands: List[Strand] = []) -> \
        List[TargetComplex]:
    complexes = [
        create_target_complex(name, strands_raw, code, strands)
        for name, strands_raw, code in zip(df.name, df.strands, df.code)
    ]
    return complexes


def get_complement_domain_name(name: str) -> str:
    if '*' in name:
        revcomp = name.replace('*', '')
        return revcomp
    else:
        revcomp = name + '*'
        return revcomp


# def get_offtarget_exclude_complexes(strands, max_size=3):
#     """Exclude a complex if one encompasses the others."""
#     exclude_complexes = []
#     t = tuple([strands]*max_size)
#     tuples = list(itertools.product(*t))
#     for t in tuples:
#
#     return