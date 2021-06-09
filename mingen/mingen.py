# -*- coding: utf-8 -*-

import re, sys
import pandas as pd

import config
from str_util import *
from features import *
from rules import *

# TODO: phonology, cross-context, impugnment, etc.


def generalize_rules_rec(Rs):
    """
    Recursively apply minimal generalization to set of FtrRules
    todo: generalize each context pair at most once
    """
    # Word-specific rules
    # Rules grouped by common change [invariant]
    R_base = {}
    for R in Rs:
        change = ' '.join(R.A) + ' -> ' + ' '.join(R.B)
        if change in R_base:
            R_base[change].append(R)
        else:
            R_base[change] = [R]
    R_base = {change: set(rules) \
                for change, rules in R_base.items()}
    R_all = {change: rules.copy() \
                for change, rules in R_base.items()}

    # First-step minimal generalization (exploit commutativity)
    print('First-step mingen ...')
    R_new = {}
    for change, rules_base in R_base.items():
        print(f'\t{change} [{len(rules_base)}]')
        rules_base = [R for R in rules_base]
        n = len(rules_base)
        rules_new = set()
        for i in range(n - 1):
            R1 = rules_base[i]
            for j in range(i + 1, n):
                R2 = rules_base[j]
                R = generalize_rules(R1, R2)
                if R is None:
                    continue
                rules_new.add(R)
        R_new[change] = rules_new
    for change in R_all:
        R_all[change] |= R_new[change]

    # Recursive minimal generalization
    for i in range(10):  # xxx loop forever
        # Report number of rules by change
        print(f'iteration {i}')

        # One-step minimal generalization
        R_old = R_new
        R_new = {}
        for change, rules_base in R_base.items():
            rules_old = R_old[change]
            print(f'\t{change} [{len(rules_base)} x {len(rules_old)}]')
            rules_new = set()
            for R1 in rules_base:
                for R2 in rules_old:
                    R = generalize_rules(R1, R2)
                    if R is None:
                        continue
                    rules_new.add(R)
            R_new[change] = (rules_new - R_all[change])

        # Update rule sets
        new_rule_flag = False
        for change in R_all:
            size_old = len(R_all[change])
            R_all[change] |= R_new[change]
            size_new = len(R_all[change])
            if size_new > size_old:
                new_rule_flag = True

        # Stop if no new rules added for any context
        if not new_rule_flag:
            break

    R_all = [R for change, rules in R_all.items() for R in rules]
    return R_all


def generalize_rules(R1, R2):
    """
    Apply minimal generalization to pair of FtrRules
    """
    # Check for matching change A -> B
    if (R1.A != R2.A) or (R1.B != R2.B):
        return None

    # Generalize left and right contexts
    C = generalize_context(R1.C, R2.C, '<-RL')
    D = generalize_context(R1.D, R2.D, 'LR->')

    R = FtrRule(R1.A, R1.B, C, D)
    return R


def generalize_context(X1, X2, direction='LR->'):
    """
    Apply minimal generalization to pair of feature contexts, working inward (<-RL) or outward (LR->) from change location
    """
    assert ((direction == 'LR->') or (direction == '<-RL'))
    if direction == '<-RL':
        X1 = X1[::-1]
        X2 = X2[::-1]

    n1 = len(X1)
    n2 = len(X2)
    n_min = min(n1, n2)
    n_max = max(n1, n2)

    Y = []
    seg_ident_flag = True
    for i in range(n_max):
        # X (Sigma*) and terminate if have exceeded shorter context
        # or have already unified features
        if (i >= n_min) or (not seg_ident_flag):
            Y.append('X')
            break
        # X (Sigma*) and terminate if either is X
        if (X1[i] == 'X') or (X2[i] == 'X'):
            Y.append('X')
            break
        # Perfect match of feature matrices
        # (NB. Conforms to A&H spec only if at least one
        # of the rules has contexts that are segment-specific)
        if X1[i] == X2[i]:
            Y.append(X1[i])
            continue
        # Unify features at first segment mismatch
        ftrs, any_match = unify_ftrs(X1[i], X2[i])
        if not any_match:
            Y.append('X')
            break
        Y.append(ftrs)
        seg_ident_flag = False

    if direction == '<-RL':
        Y = Y[::-1]

    Y = tuple(Y)
    return Y
