# -*- coding: utf-8 -*-

import numpy as np

import config
from rules import *
from str_util import *
import pynini_util


def rate_wugs(wugs, rules, score_type='confidence'):
    print('Wug test ...')
    # Symbol environment
    syms = [x for x in config.seg2ftrs]
    sigstar, symtable = pynini_util.sigstar(syms)

    stems = [str(x) for x in wugs['stem']]
    outputs = [str(x) for x in wugs['output']]
    wordforms = list(zip(stems, outputs))

    R_all = [FtrRule.from_str(R) for R in rules['rule']]
    R_all = [(R, score, idx) for (R, score, idx) \
        in zip(R_all, rules[score_type], rules['rule_idx'])]

    max_rating = {}
    max_rule = {}
    print('iter')
    for i, R_ in enumerate(R_all):
        if i % 500 == 0:
            print(i)

        # Convert rule to segment regexes
        R, score, rule_idx = R_
        (A, B, C, D) = R.regexes()

        # Subset of wug data s.t. CAD occurs in input
        CAD = [Z for Z in [C, A, D] if Z != '∅']
        CAD = ' '.join(CAD)
        if CAD != '':
            subdat = [wf for wf in wordforms if re.search(CAD, wf[0])]
        else:
            subdat = wordforms
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
            if (wf1, wf2) not in max_rating \
                or score > max_rating[(wf1, wf2)]:
                max_rating[(wf1, wf2)] = score
                max_rule[(wf1, wf2)] = R_

    # Results
    print()
    wug_ratings = []
    for wf, rating in max_rating.items():
        wf1, wf2 = wf
        R, score, rule_idx = max_rule[(wf1, wf2)]
        print(wf1, wf2, rating)
        print(R)
        print()
        wug_ratings.append((wf1, wf2, rating, rule_idx))
    return wug_ratings
