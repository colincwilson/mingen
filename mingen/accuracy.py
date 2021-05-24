# -*- coding: utf-8 -*-

import config
from rules import *
import pynini_util


def score_rules(R_all):
    """
    Hits and scope for FtrRules on training data
    """

    # Convert rules to Pynini cdrewrites
    syms = [x for x in config.seg2ftrs]
    symtable = pynini_util.symtable(syms)
    sigstar = pynini_util.sigstar(symtable)

    #input1 = config.dat_train['wordform1'][0]  # xxx test input
    input1 = '⋊ ɪ n v ɛ n t ⋉'
    print(input1)
    input1 = pynini_util.accep(input1, symtable)

    R_fst = []
    for R in R_all:
        R = repr(R)
        print(R)
        AB, CD = R.split(' / ')
        A, B = AB.split(' -> ')
        C, D = CD.split(' __ ')
        R = pynini_util.compile_rule(A, B, C, D, sigstar, symtable)
        R_fst.append(R)

        output1 = input1 @ R
        print(output1.print())
        strpath_iter = output1.paths(input_token_type=symtable,
                                     output_token_type=symtable)
        print([x for x in strpath_iter.ostrings()])

    return None


def score_rule(R):
    """
    Hits and scope for FtrRule on training data 
    todo: use pynini
    """
    hit = 0
    scope = 0
    for i in range(len(config.dat_train)):
        wordform1 = config.dat_train['wordform1'][i]
        wordform2 = config.dat_train['wordform2'][i]

        print(str(R))
        print(wordform1)

        predicted, apply_flag = apply_rule(R, wordform1.split(' '))
        if not apply_flag:
            continue
        print(predicted[0], wordform2)
        if (' '.join(predicted[0]) == wordform2):
            hit += 1
        scope += 1
        sys.exit(0)
    return (hit, scope)