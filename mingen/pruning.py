# -*- coding: utf-8 -*-

import sys
from functools import lru_cache
from features import *
from rules import *


def prune_rules(rules, rule_score='confidence'):
    print('Prune ...')
    rules = rules.sort_values(by=rule_score, ascending=True)
    R_all = [FtrRule.from_str(R) for R in rules['rule']]
    R_all = [(R, score, idx) for (R, score, idx) \
        in zip(R_all, rules[rule_score], rules['rule_idx'])]

    print('iter #pruned')
    pruned = []  # Non-maximal rules (can contain duplicates)
    n = len(R_all)
    for i in range(n - 1):
        if i % 500 == 0:
            print(i, len(pruned))
        Ri_ = R_all[i]
        for j in range(n - 1, i + 1, -1):
            Rj_ = R_all[j]
            cmp = rule_cmp(Ri_, Rj_)
            if cmp == +1:
                pruned.append(Rj_)
            if cmp == -1:
                pruned.append(Ri_)
                break

    print(f'{len(pruned)} pruned rules')  # 30261 pruned rules

    # Rules that are maximal wrt rule_cmp
    idx_pruned = [idx for (R, score, idx) in pruned]
    rules_max = rules[~(rules['rule_idx'].isin(idx_pruned))]
    rules_max = rules_max.sort_values(by=rule_score, ascending=False)
    return rules_max


def rule_cmp(R1_, R2_):
    """ Compare rules by score and generality, each breaking ties for the other
        +1 if score1 > score2 and R1 ⊒ R2 -or- score1 = score2 and R1 ⊐ R2
        -1 if score2 > score1 and R2 ⊒ R1 -or- score1 = score2 and R2 ⊐ R1
        0 otherwise
    """
    R1, score1, idx1 = R1_
    R2, score2, idx2 = R2_

    # R1 has higher score
    if score1 > score2:
        if rule_mgt(R1, R2):
            return +1
    elif score2 > score1:
        if rule_mgt(R2, R1):
            return -1
    else:
        mgt12 = rule_mgt(R1, R2)
        mgt21 = rule_mgt(R2, R1)
        if mgt12 and not mgt21:
            return +1
        if mgt21 and not mgt12:
            return -1
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
