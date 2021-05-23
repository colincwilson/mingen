# -*- coding: utf-8 -*-

import config
from rules import *


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