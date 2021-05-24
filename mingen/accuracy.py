# -*- coding: utf-8 -*-

import config
from rules import *
from util import *
import pynini_util


def score_rules(R_all):
    """
    Hits and scope for FtrRules on training data
    todo: precompile inputs, apply to all simultaneously?
    """

    # Symbol environment
    syms = [x for x in config.seg2ftrs]
    sigstar, symtable = pynini_util.sigstar(syms)

    # Organize rules by left-hand context
    print('Organizing rules ...')
    R_parts = []
    Cmap = {}
    for R_id, R in enumerate(R_all):
        R_ = repr(R)
        AB, CD = R_.split(' / ')
        A, B = AB.split(' -> ')
        B = ' '.join(['⟨', B, '⟩'])  # Mark rewrite loci
        C, D = CD.split(' __ ')
        R_parts.append((A, B, C, D))

        if C in Cmap:
            Cmap[C].append(R_id)
        else:
            Cmap[C] = [R_id]

    # Process forms matching each left-hand context
    print("Computing hit / scope ...")
    dat = config.dat_train
    wordform1 = [str(x) for x in dat['wordform1']]
    wordform2 = [str(x) for x in dat['wordform2']]
    wordforms = list(zip(wordform1, wordform2))

    hits = [0.0] * len(R_all)
    scopes = [0.0] * len(R_all)
    for C in Cmap:
        subdat = [(wf1, wf2) for (wf1, wf2) in wordforms if re.search(C, wf1)]
        for R_id in Cmap[C]:
            (A, B, C, D) = R_parts[R_id]

            R_ = pynini_util.compile_rule(A, B, C, D, sigstar, symtable)
            R_hits = 0.0
            R_scope = 0.0

            subdat_ = [(wf1, wf2) for (wf1, wf2) \
                        in subdat if re.search(A, wf1)]
            subdat_ = [(wf1, wf2) for (wf1, wf2) \
                        in subdat_ if re.search(D, wf1)]
            if len(subdat_) == 0:
                print(f'zero scope for {C}, {A}, {D}')
                sys.exit(0)

            for (wf1, wf2) in subdat_:
                input1 = pynini_util.accep(wf1, symtable)
                output1 = input1 @ R_
                strpath_iter = output1.paths(input_token_type=symtable,
                                             output_token_type=symtable)
                output1 = [x for x in strpath_iter.ostrings()][0]  # xxx

                if not re.search('⟨.*⟩', output1):
                    continue

                R_scope += 1.0
                output1 = re.sub('⟨ | ⟩', '', output1)
                if output1 == wf2:
                    R_hits += 1.0
                    #print(f'hit: {output1} == {wf2}')
                else:
                    print(f'miss: {output1} != {wf2}')
            hits[R_id] = R_hits
            scopes[R_id] = R_scope
            print(f'rule {R_id}, hits = {R_hits}, scope = {R_scope}, '
                  f'accuracy = {R_hits/R_scope}')

    return hits, scopes
