import traceback
from typing import List

from nupack import *

from src.nupack import utils as nutils


class DesignRunner:
    def __init__(self, model_params: dict = None):
        if model_params is None:
            model_params = {
                'material': 'dna',
                'celsius': 37,
                'sodium': 0.5,
                'magnesium': 0.1
            }
        self.model = Model(**model_params)

    def build_domains(self, domains_data: List[dict]) -> List[Domain]:
        """Build NUPACK domains from domain data"""
        domains = []
        for d in domains_data:
            domain = nutils.create_domain(d['name'], d['code'])
            domains.append(domain)
        return domains

    def build_strands(self, strands_data: List[dict], domains: List[Domain]) -> \
            List[TargetStrand]:
        """Build NUPACK strands from strand data"""
        strands = []
        for s in strands_data:
            strand = nutils.create_target_strand(s['name'], s['domains'],
                                                 domains, sep=',')
            strands.append(strand)
        return strands

    def build_complexes(self, complexes_data: List[dict],
                        strands: List[TargetStrand]) -> List[TargetComplex]:
        """Build NUPACK complexes from complex data"""
        complexes = []
        for c in complexes_data:
            complex_obj = nutils.create_target_complex(
                c['name'], c['strands'], c['structure'], strands, sep=','
            )
            complexes.append(complex_obj)
        return complexes

    def parse_constraint_params(self, constraint: dict, domains: List[Domain],
                                strands: List[TargetStrand]) -> dict:
        """Parse constraint parameters and resolve domain/strand references"""
        params = constraint['params'].copy()

        # Resolve domain references
        if 'domains' in params and isinstance(params['domains'], str):
            domain_names = [d.strip() for d in params['domains'].split(',') if
                            d.strip()]
            domain_objs = []
            for dname in domain_names:
                dname_clean = dname.replace('~', '')
                domain_obj = nutils.extract_domain_by_name(dname_clean, domains)
                if dname.startswith('~'):
                    domain_objs.append(~domain_obj)
                else:
                    domain_objs.append(domain_obj)
            params['domains'] = domain_objs

        # Similar handling for domains1, domains2
        for key in ['domains1', 'domains2']:
            if key in params and isinstance(params[key], str):
                domain_names = [d.strip() for d in params[key].split(',') if
                                d.strip()]
                domain_objs = []
                for dname in domain_names:
                    dname_clean = dname.replace('~', '')
                    domain_obj = nutils.extract_domain_by_name(dname_clean,
                                                               domains)
                    if dname.startswith('~'):
                        domain_objs.append(~domain_obj)
                    else:
                        domain_objs.append(domain_obj)
                params[key] = domain_objs

        # Resolve scope if it's a domain list
        if 'scope' in params and isinstance(params['scope'], str):
            scope_names = [d.strip() for d in params['scope'].split(',') if
                           d.strip()]
            if scope_names:
                scope_objs = []
                for sname in scope_names:
                    sname_clean = sname.replace('~', '')
                    scope_objs.append(
                        nutils.extract_domain_by_name(sname_clean, domains))
                params['scope'] = scope_objs
            print(f"=== Inside scope: {params}")

        # Parse patterns list
        if 'patterns' in params and isinstance(params['patterns'], str):
            params['patterns'] = [p.strip() for p in
                                  params['patterns'].split(',') if p.strip()]

        # Parse limits
        if 'limits' in params and isinstance(params['limits'], str):
            params['limits'] = [float(x.strip()) for x in
                                params['limits'].split(',')]

        # Parse catalog
        if 'catalog' in params and isinstance(params['catalog'], str):
            params['catalog'] = [[x.strip()] for x in
                                 params['catalog'].split(',')]

        # Resolve source strands
        if 'sources' in params and isinstance(params['sources'], str):
            source_names = [s.strip() for s in params['sources'].split(',') if
                            s.strip()]
            params['sources'] = [nutils.extract_strand_by_name(sn, strands) for
                                 sn in source_names]

        # Convert numeric strings to appropriate types
        for key in ['word', 'types', 'energy_ref']:
            if key in params and isinstance(params[key], str):
                params[key] = int(params[key]) if key in ['word',
                                                          'types'] else float(
                    params[key])

        for key in ['weight']:
            if key in params and isinstance(params[key], str):
                params[key] = float(params[key])

        return params

    def build_constraint(self, constraint: dict, domains: List[Domain],
                         strands: List[TargetStrand]):
        """Build a NUPACK constraint object"""
        params = self.parse_constraint_params(constraint, domains, strands)
        print(f"+==+ params: {params}")

        ctype = constraint['type']
        is_hard = constraint['is_hard']

        try:
            if ctype == "Pattern":
                patterns = params.get('patterns', [])
                scope = params.get('scope', None)
                weight = params.get('weight', 1.0) if not is_hard else None
                if is_hard:
                    return Pattern(patterns, scope=scope) if scope else Pattern(
                        patterns)
                else:
                    return Pattern(patterns, scope=scope,
                                   weight=weight) if scope else Pattern(
                        patterns, weight=weight)

            elif ctype == "Diversity":
                word = params.get('word')
                types = params.get('types')
                scope = params.get('scope', None)
                return Diversity(word=word, types=types,
                                 scope=scope) if scope else Diversity(word=word,
                                                                      types=types)

            elif ctype == "Match":
                return Match(params['domains1'], params['domains2'])

            elif ctype == "Complementarity":
                wobble = params.get('wobble_mutations', False)
                return Complementarity(params['domains1'], params['domains2'],
                                       wobble_mutations=wobble)

            elif ctype == "Similarity":
                domains = params['domains']
                source = params['source']
                limits = params.get('limits', [0.0, 1.0])
                weight = params.get('weight', 1.0) if not is_hard else None
                if is_hard:
                    return Similarity(domains, source, limits=limits)
                else:
                    return Similarity(domains, source, limits=limits,
                                      weight=weight)

            elif ctype == "Library":
                return Library(params['domains'], catalog=params['catalog'])

            elif ctype == "Window":
                return Window(params['domains'], sources=params['sources'])

            elif ctype == "SSM":
                word = params['word']
                scope = params.get('scope', None)
                weight = params.get('weight', 0.3)
                return SSM(word=word, scope=scope,
                           weight=weight) if scope else SSM(word=word,
                                                            weight=weight)

            elif ctype == "EnergyMatch":
                domains = params['domains']
                energy_ref = params.get('energy_ref', None)
                weight = params.get('weight', 1.0)
                if energy_ref is not None:
                    return EnergyMatch(domains, energy_ref=energy_ref,
                                       weight=weight)
                else:
                    return EnergyMatch(domains, weight=weight)

        except Exception as e:
            raise ValueError(f"Failed to build constraint {ctype}: {str(e)}")

    def build_off_targets(self, off_target_config: dict,
                          strands: List[TargetStrand]) -> SetSpec:
        """Build SetSpec for off_targets with max_size and excludes"""
        max_size = off_target_config.get('max_size', 3)
        excludes_data = off_target_config.get('excludes', [])

        # Convert excludes from list of strand name lists to list of strand object lists
        excludes = []
        for exclude_group in excludes_data:
            strand_group = []
            for strand_name in exclude_group:
                strand_obj = nutils.extract_strand_by_name(strand_name, strands)
                strand_group.append(strand_obj)
            excludes.append(strand_group)

        return SetSpec(max_size=max_size, exclude=excludes)

    def run_design(self, job_data: dict) -> dict:
        """Run the NUPACK design job"""
        try:
            # Build domains (filter out complement domains starting with ~)
            base_domains_data = [d for d in job_data['domains'] if
                                 not d['name'].startswith('~')]
            domains = self.build_domains(base_domains_data)

            # Build strands
            strands = self.build_strands(job_data['strands'], domains)

            # Build complexes
            complexes = self.build_complexes(job_data['complexes'], strands)

            # Build concentrations
            base_conc = job_data.get('base_concentration', 1e-7)
            concentrations = {c: base_conc for c in complexes}
            # Build concentrations
            custom_concentrations = job_data.get('custom_concentrations', {})

            for c in complexes:
                # Use custom concentration if specified, otherwise use base_conc
                if c.name in custom_concentrations:
                    concentrations[c] = float(custom_concentrations[c.name])
                else:
                    concentrations[c] = base_conc

            # Build constraints
            hard_constraints = []
            for hc in job_data.get('hard_constraints', []):
                print("===> hc: ", hc)
                hard_constraints.append(
                    self.build_constraint(hc, domains, strands)
                )

            soft_constraints = []
            for sc in job_data.get('soft_constraints', []):
                soft_constraints.append(
                    self.build_constraint(sc, domains, strands)
                )

            # Build off_targets with SetSpec
            off_target_config = job_data.get('off_targets',
                                             {'max_size': 3, 'excludes': []})
            off_targets_spec = self.build_off_targets(off_target_config,
                                                      strands)

            # Create tube with off_targets
            tube = TargetTube(
                on_targets=concentrations,
                name='tube1',
                off_targets=off_targets_spec
            )

            # Design options
            options = DesignOptions(
                f_stop=job_data.get('f_stop', 0.01),
                seed=job_data.get('seed', 93)
            )

            # Run design
            design = tube_design(
                tubes=[tube],
                model=self.model,
                options=options,
                hard_constraints=hard_constraints,
                soft_constraints=soft_constraints
            )

            results = design.run(trials=job_data.get('trials', 3))[0]

            # Extract results
            result_domains = []
            for domain_name, sequence in results.to_analysis.domains.items():
                result_domains.append({
                    'name': domain_name.name,
                    'sequence': str(sequence)
                })

            result_strands = []
            for strand_name, sequence in results.to_analysis.strands.items():
                result_strands.append({
                    'name': strand_name.name,
                    'sequence': str(sequence)
                })

            return {
                'success': True,
                'result_domains': result_domains,
                'result_strands': result_strands,
                'raw_output': str(results)
            }

        except Exception as e:
            return {
                'success': False,
                'error': f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
            }