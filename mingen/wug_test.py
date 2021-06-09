# -*- coding: utf-8 -*-

import numpy as np

import config
from rules import *
from str_util import *
import pynini_util


def rate_wugs(wugs, rules, rule_score='confidence'):
    # Symbol environment
    syms = [x for x in config.seg2ftrs]
    sigstar, symtable = pynini_util.sigstar(syms)

    stems = [str(x) for x in wugs['stem']]
    outputs = [str(x) for x in wugs['output']]
    wordforms = list(zip(stems, outputs))
    max_rating = {}
    max_rating_idx = {}

    R_all = [FtrRule.from_str(R) for R in rules['rule']]
    score_all = [score for score in rules[rule_score]]

    for idx, R in enumerate(R_all):
        if idx % 500 == 0:
            print(idx)

        # Convert rule to segment regexes
        (A, B, C, D) = R.regexes()
        score = score_all[idx]

        # Subset of wug data s.t. CAD occurs in input
        CAD = [Z for Z in [C, A, D] if Z != '∅']
        CAD = ' '.join(CAD)
        subdat = [wf for wf in wordforms if re.search(CAD, wf[0])] \
            if CAD != '' else wordforms
        if len(subdat) == 0:
            continue

        # Compile rule to FST
        R_fst = pynini_util.compile_rule(A, B, C, D, sigstar, symtable)

        for (wf1, wf2) in subdat:
            # Apply rule to input
            input1 = pynini_util.accep(wf1, symtable)
            output1 = input1 @ R_fst
            strpath_iter = output1.paths(
                input_token_type=symtable, output_token_type=symtable)
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
            if ((wf1, wf2) not in max_rating) \
                    or (score > max_rating[(wf1, wf2)]):
                max_rating[(wf1, wf2)] = score
                max_rating_idx[(wf1, wf2)] = idx

    # Results
    print()
    wug_ratings = []
    for wf in max_rating.keys():
        wf1, wf2 = wf
        rating = max_rating[wf]
        rule_idx = max_rating_idx[wf]
        R = R_all[rule_idx]
        print(wf1, wf2, rating)
        print(R)
        print()
        wug_ratings.append((wf1, wf2, rating, rule_idx))
    return wug_ratings
