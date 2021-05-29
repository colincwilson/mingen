# -*- coding: utf-8 -*-

import config
from rules import *
from str_util import *
import pynini_util


def score_rules(R_all):
    """
    Hits and scope for FtrRules on training data
    todo: precompile inputs, apply to all simultaneously?
    """

    # Symbol environment
    syms = [x for x in config.seg2ftrs]
    sigstar, symtable = pynini_util.sigstar(syms)

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
        B = ' '.join(['⟨', B, '⟩'])  # Mark rewrite loci
        C, D = CD.split(' __ ')

        R_parse.append((A, B, C, D))
        if C in C_map:
            C_map[C].append(idx)
        else:
            C_map[C] = [idx]

    # Hits and scope for each rule
    print("Computing hit / scope ...")
    dat = config.dat_train
    wordform1 = [str(x) for x in dat['wordform1']]
    wordform2 = [str(x) for x in dat['wordform2']]
    wordforms = list(zip(wordform1, wordform2))

    hits_all = [0.0] * len(R_all)
    scopes_all = [0.0] * len(R_all)
    for C in C_map:
        # Subset of data s.t. left-hand context occurs in input
        subdat = filter(lambda wf: re.search(C, wf[0]), wordforms)

        for idx in C_map[C]:
            # Compile rule to FST
            (A, B, C, D) = R_parse[idx]
            R_fst = pynini_util.compile_rule(A, B, C, D, sigstar, symtable)

            # Subset of data s.t. right-hand context occurs in input
            subdat_ = filter(lambda wf: re.search(D, wf[0]), subdat)

            hits = 0.0
            scope = 0.0
            # Loop over input/output pairs in data
            for (wf1, wf2) in subdat_:
                #print(wf1, '->', wf2)
                # Apply rule to input and yield first (xxx) output
                input1 = pynini_util.accep(wf1, symtable)
                output1 = input1 @ R_fst
                strpath_iter = output1.paths(input_token_type=symtable,
                                             output_token_type=symtable)
                output1 = [x for x in strpath_iter.ostrings()][0]  # xxx

                # Detect locus of application
                if not re.search('⟨.*⟩', output1):  # Did not apply!
                    continue

                scope += 1.0

                # Remove markers on locus of application
                output1 = re.sub('⟨ ', '', output1)
                output1 = re.sub(' ⟩', '', output1)

                # Hit (exact match to output) or miss
                if output1 == wf2:
                    hits += 1.0
                    #print(f'hit: {output1} == {wf2}')
                else:
                    pass
                    #print(f'miss: {output1} != {wf2}')

            hits_all[idx] = hits
            scopes_all[idx] = scope
            try:
                print(f'rule {idx}, hits = {hits}, scope = {scope}, '
                      f'accuracy = {hits/scope}')
            except:
                print('error: rule has zero scope')
                print(R_all[idx])
                print(repr(R_all[idx]))

    return hits_all, scopes_all
