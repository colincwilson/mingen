# -*- coding: utf-8 -*-

import config
from scipy.stats import t as student_t

from rules import *
from str_util import *
import pynini_util


def group_rules(R_all):
    # Parse rules and group rules by common left-hand context
    # (allows filtering out data to which rule does not apply)
    print('Grouping rules by left-hand context ...')
    R_parse = []
    C_map = {}
    for idx, R in enumerate(R_all):
        # Convert rule to explicit regexp formant
        R_regex = repr(R)
        AB, CD = R_regex.split(' / ')
        A, B = AB.split(' -> ')
        C, D = CD.split(' __ ')
        R_parse.append((A, B, C, D))

        if C in C_map:
            C_map[C].append(idx)
        else:
            C_map[C] = [idx]
    #for C in C_map:
    #    print(C)
    #    for idx in C_map[C]:
    #        print('\t', R_parse[idx])
    return R_parse, C_map


def score_rules(R_all):
    """
    Hits and scope for FtrRules on training data
    todo: precompile inputs, apply to all simultaneously?
    """
    # xxx grouping no longer used, only need to parse
    R_parse, C_map = group_rules(R_all)

    # Symbol environment
    syms = [x for x in config.seg2ftrs]
    sigstar, symtable = pynini_util.sigstar(syms)

    # Precompile inputs to FSTs
    dat = config.dat_train
    stems = [str(x) for x in dat['stem']]
    outputs = [str(x) for x in dat['output']]
    stem_ids = list(range(len(dat)))
    wordforms = list(zip(stems, outputs, stem_ids))
    stem_fsts = pynini_util.accep(stems, symtable)

    # Hits and scope for each rule
    print("Computing hit / scope ...")

    hits_all = [0.0] * len(R_all)
    scope_all = [0.0] * len(R_all)
    for C in C_map:
        # Subset of data s.t. left-hand context occurs in input
        #subdat = [wf for wf in wordforms if re.search(C, wf[0])] \
        #    if C != '∅' else wordforms
        #print(f'C = {C}, size of data subset {len(subdat)}')

        for idx in C_map[C]:
            # Compile rule to FST
            (A, B, C, D) = R_parse[idx]
            R_fst = pynini_util.compile_rule(A, B, C, D, sigstar, symtable)

            # Subset of data s.t. CAD occurs in input
            CAD = [X for X in [C, A, D] if X != '∅']
            CAD = ' '.join(CAD)
            subdat = [wf for wf in wordforms if re.search(CAD, wf[0])] \
                if CAD != '' else wordforms

            # By construction, rules with scopes of 1 or 2
            # are fully accurate xxx check
            if len(subdat) < 3:
                hits_all[idx] = len(subdat)
                scope_all[idx] = len(subdat)
                continue

            # Loop over input/output pairs in data subset
            hits = 0.0
            scope = 0.0
            for (wf1, wf2, stem_id) in subdat:
                #print(wf1, '->', wf2)
                # Apply rule to input and yield first (xxx) output
                #input1 = pynini_util.accep(wf1, symtable)

                input1 = stem_fsts[stem_id]
                output1 = input1 @ R_fst
                strpath_iter = output1.paths(input_token_type=symtable,
                                             output_token_type=symtable)
                output1 = [x for x in strpath_iter.ostrings()][0]  # xxx

                # Check whether rule applied
                if not re.search('⟨', output1):
                    continue

                scope += 1.0

                # Remove markers around locus of application
                output1 = delete_markers(output1)

                # Hit (exact match to output) or miss
                if output1 == wf2:
                    hits += 1.0
                    #print(f'hit: {output1} == {wf2}')
                else:
                    pass
                    #print(f'miss: {output1} != {wf2}')

            hits_all[idx] = hits
            scope_all[idx] = scope
            if hits == 0.0:
                print('(warning) rule has zero hits')
                print(R_all[idx])
                print(repr(R_all[idx]))
            if scope == 0.0:
                print('(error) rule has zero scope')
                print(f'size of data subset_ {len(subdat_)}')
                print(R_all[idx])
                print(repr(R_all[idx]))
                sys.exit(0)
            print(f'rule {idx}, hits = {hits}, scope = {scope}, '
                  f'reliability = {hits/scope}')

    return hits_all, scope_all


def confidence(hits, scope, alpha=0.55):
    """
    Adjust reliability by scope
    (default alpha from A&H 2003:127)
    """
    # Adjusted reliability
    p_star = (hits + 0.5) / (scope + 1.0)
    # Estimated variance
    var_est = (p_star * (1 - p_star)) / scope
    var_est = var_est**0.5
    # Confidence
    z = student_t.ppf(alpha, scope - 1.0)
    c = p_star - z * var_est
    return c


def test():
    # Exampes from A&H 2003:127
    hits, scope = 5.0, 5.0
    print(confidence(hits, scope, alpha=0.75))
    hits, scope = 1000, 1000.0
    print(confidence(hits, scope, alpha=0.75))


if __name__ == "__main__":
    test()