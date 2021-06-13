# -*- coding: utf-8 -*-

import sys
import numpy as np
from collections import namedtuple
from functools import lru_cache
from features import *
from rules import *

ScoredRule = namedtuple('ScoredRule', ['R', 'score', 'length', 'idx'])


def prune_rules(rules, score_type='confidence', digits=10):
    print('Prune ...')
    rules = rules.sort_values(by=score_type, ascending=False)
    R_all = [ScoredRule(FtrRule.from_str(R),
                        np.round(score, digits),
                        len(R),
                        idx) \
        for (R, score, idx) \
            in zip(rules['rule'], rules[score_type], rules['rule_idx'])]

    i = 0
    pruned = []  # Non-maximal rules
    print('iter pruned')
    while len(R_all) > 0:
        if i > 0 and i % 100 == 0:
            print(i, len(pruned))
        Ri_ = R_all.pop(0)
        prune_flag = False
        for j, Rj_ in enumerate(R_all):
            cmp = rule_cmp(Ri_, Rj_)
            if cmp == -1:
                pruned.append(Rj_)
                R_all[j] = None
            if cmp == +1:
                prune_flag = True
        if prune_flag:
            pruned.append(Ri_)
        R_all = [R for R in R_all if R is not None]
        i += 1

    print(f'{len(pruned)} pruned rules')  # 30261 pruned rules

    # Keep rules that are maximal wrt rule_cmp
    idx_pruned = [R.idx for R in pruned]
    rules_max = rules[~(rules['rule_idx'].isin(idx_pruned))]
    rules_max = rules_max.sort_values(by=score_type, ascending=False)
    return rules_max


def rule_cmp(R1_: ScoredRule, R2_: ScoredRule):
    """ Compare rules by score and generality, breaking ties with length
        -1 if score1 > score2 and R1 ⊒ R2   -or-
              score1 == score2 and R1 ⊐ R2  -or-
              score1 == score2 and R1 = R2 and length1 < length2
        +1 if score2 > score1 and R2 ⊒ R1   -or-
              score2 == score1 and R2 ⊐ R1  -or-
              score2 == score1 and R2 = R1 and length2 < length1
        0 otherwise
    """
    R1, score1, length1, idx1 = R1_
    R2, score2, length2, idx2 = R2_

    # R1 has higher score
    if score1 > score2:
        if rule_mgt(R1, R2):
            return -1
    # R2 has higher score
    elif score2 > score1:
        if rule_mgt(R2, R1):
            return +1
    # Tied on score
    else:
        mgt12 = rule_mgt(R1, R2)
        mgt21 = rule_mgt(R2, R1)
        if mgt12:
            if not mgt21 or length1 < length2:
                return -1
        if mgt21:
            if not mgt12 or length2 < length1:
                return +1
    return 0


def rule_mgt(R1: FtrRule, R2: FtrRule):
    """ More-general-than-or-equal relation ⊒ on rules """
    # Apply only to rules with same focus and change xxx fixme
    if (R1.A != R2.A) or (R1.B != R2.B):
        return False

    if not context_mgt(R1.C, R2.C, '<-RL'):
        return False

    if not context_mgt(R1.D, R2.D, 'LR->'):
        return False

    return True


#@lru_cache(maxsize=1024)
def context_mgt(Z1, Z2, direction='LR->'):
    """
    More-general-than-or-equal relation ⊒ on rule contexts (sequences of feature matrices), inward (<-RL) or outward (LR->) from change location
    """
    assert ((direction == 'LR->') or (direction == '<-RL'))
    if direction == '<-RL':
        Z1 = Z1[::-1]
        Z2 = Z2[::-1]
    n1 = len(Z1)
    n2 = len(Z2)

    # Empty context is always more general
    if n1 == 0:
        return True

    # Longer context cannot be more general
    # (except for special case below)
    if (n1 - n2) > 1:
        return False

    for i in range(n1):
        # Special case: context Z1 has one more matrix than Z2,
        # test whether it is identical to X (Sigma*)
        if i == n2:
            return (Z1[i] == 'X')

        # Matrix Z1[i] is not more general than Z2[i]
        if not subsumes(Z1[i], Z2[i]):
            return False

    return True


def test():
    rule1 = ScoredRule(
        FtrRule.from_str(
            "∅ -> d / X [-spread.gl] [-C/V, +syllabic, -consonantal, +sonorant, +continuant, +approximant, -nasal, +voice, -spread.gl, -LABIAL, -round, -labiodental, -CORONAL, -lateral, +DORSAL, -high, -low, +front, -back, -tense] [+C/V, -syllabic, -consonantal, +sonorant, +continuant, +approximant, -nasal, +voice, -spread.gl, -LABIAL, -round, -labiodental, +CORONAL, -anterior, +distributed, -strident, -lateral, -DORSAL] __ [-begin/end]"
        ), 0.9978736, -1, 1)
    rule2 = ScoredRule(
        FtrRule.from_str(
            "∅ -> d / X [-spread.gl, -lateral] [-C/V, +syllabic, -consonantal, +sonorant, +continuant, +approximant, -nasal, +voice, -spread.gl, -LABIAL, -round, -labiodental, -CORONAL, -lateral, +DORSAL, -high, -low, +front, -back, -tense] [+C/V, -syllabic, -consonantal, +sonorant, +continuant, +approximant, -nasal, +voice, -spread.gl, -LABIAL, -round, -labiodental, +CORONAL, -anterior, +distributed, -strident, -lateral, -DORSAL] __ [-begin/end]"
        ), 0.9978424, -1, 2)
    print(rule_cmp(rule1, rule2))