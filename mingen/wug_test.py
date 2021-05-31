# -*- coding: utf-8 -*-

import config
from rules import *
from str_util import *
import pynini_util
from reliability import group_rules


def score_mappings(wug_dat, rules):
    # Symbol environment
    syms = [x for x in config.seg2ftrs]
    sigstar, symtable = pynini_util.sigstar(syms)

    stems = [str(x) for x in wug_dat['stem']]
    outputs = [str(x) for x in wug_dat['output']]
    wordforms = list(zip(stems, outputs))
    max_score = {}
    max_score_idx = {}

    # Parsed regex rules grouped by left-hand side
    R_all = [str2ftr_rule(R) for R in rules['rule']]
    score_all = [score for score in rules['reliability']]
    #R_parse, C_map = group_rules(R_all)

    for idx, R in enumerate(R_all):
        if idx % 500 == 0:
            print(idx)
        # Convert rule to explicit regexp format
        R_regex = repr(R)
        AB, CD = R_regex.split(' / ')
        A, B = AB.split(' -> ')
        C, D = CD.split(' __ ')

        # Subset of wug data s.t. CAD occurs in input
        CAD = [X for X in [C, A, D] if X != '∅']
        CAD = ' '.join(CAD)
        subdat = [wf for wf in wordforms if re.search(CAD, wf[0])] \
            if CAD != '' else wordforms
        if len(subdat) == 0:
            continue

        # Compile rule to FST
        R_fst = pynini_util.compile_rule(A, B, C, D, sigstar, symtable)
        score = score_all[idx]

        for (wf1, wf2) in subdat:
            # Apply rule to input
            input1 = pynini_util.accep(wf1, symtable)
            output1 = input1 @ R_fst
            strpath_iter = output1.paths(input_token_type=symtable,
                                         output_token_type=symtable)
            output1 = [x for x in strpath_iter.ostrings()][0]  # xxx

            # Check whether rule applied
            if not re.search('⟨.*⟩', output1):
                continue

            # Remove markers around locus of application
            output1 = re.sub('⟨ ', '', output1)
            output1 = re.sub(' ⟩', '', output1)

            # Update only if exact match and better than previous score
            if output1 != wf2:
                continue
            if ((wf1, wf2) not in max_score) \
                    or (score > max_score[(wf1, wf2)]):
                max_score[(wf1, wf2)] = score
                max_score_idx[(wf1, wf2)] = idx

    # Report results
    print()
    wug_scores = []
    for wf in max_score.keys():
        wf1, wf2 = wf
        score = max_score[wf]
        idx = max_score_idx[wf]
        R = R_all[idx]
        print(wf1, wf2, score)
        print(R)
        print()
        wug_scores.append((wf1, wf2, score, idx))
    return wug_scores
