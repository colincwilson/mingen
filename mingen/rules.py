# -*- coding: utf-8 -*-

import config
from features import *


class SegRule():
    """ Rule stated over segments """

    def __init__(self, A, B, C, D):
        self.A = A
        self.B = B
        self.C = C
        self.D = D

    def __str__(self):
        parts = {'A': self.A, 'B': self.B, 'C': self.C, 'D': self.D}
        parts = {X: ' '.join(parts[X]) for X in parts}
        parts = {X: '∅' if val == '' else val for X, val in parts.items()}
        return f"{parts['A']} -> {parts['B']} / {parts['C']} __ {parts['D']}"


class FtrRule():
    """
    Rule with contexts defined by features and X (Sigma*)
    [immutable]
    """

    def __init__(self, A, B, C, D):
        self.A = A
        self.B = B
        self.C = C
        self.D = D
        self._hash = self.__hash__()

    def __eq__(self, other):
        if not isinstance(other, FtrRule):
            return False
        return (self.A == other.A) and (self.B == other.B) \
                and (self.C == other.C) and (self.D == other.D)

    def __hash__(self):
        if hasattr(self, '_hash'):
            return self._hash
        _hash = 7 * hash(self.A) + 13 * hash(self.B) + 17 * hash(
            self.C) + 19 * hash(self.D)
        return _hash

    def __str__(self):
        """ String with feature matrices """
        if hasattr(self, '_str'):
            return self._str
        parts1 = {'A': self.A, 'B': self.B}
        parts1 = {X: ' '.join(parts1[X]) for X in parts1}
        parts1 = {X: '∅' if val == '' else val for X, val in parts1.items()}

        parts2 = {'C': self.C, 'D': self.D}
        parts2 = {X: ftrs2str(parts2[X]) for X in parts2}

        return (f"{parts1['A']} -> {parts1['B']} / "
                f"{parts2['C']} __ {parts2['D']}")

    def __repr__(self):
        """ String with segment regexs """
        if hasattr(self, '_repr'):
            return self._repr
        parts1 = {'A': self.A, 'B': self.B}
        parts1 = {X: ' '.join(parts1[X]) for X in parts1}
        parts1 = {X: '∅' if val == '' else val for X, val in parts1.items()}

        parts2 = {'C': self.C, 'D': self.D}
        parts2 = {X: ftrs2regex(parts2[X]) for X in parts2}

        return (f"{parts1['A']} -> {parts1['B']} / "
                f"{parts2['C']} __ {parts2['D']}")


def str2rule(x):
    """
    Create FtrRule from string with feature matrices
    """
    A, rest = x.split(' -> ')
    B, rest = rest.split(' / ')
    C, D = rest.split(' __ ')
    R = FtrRule(A, B, str2ftrs(C), str2ftrs(D))
    print(str(R))
    return R


def apply_rule(R, x):
    """
    Apply FtrRule A -> B / C __ D at all positions in segment sequence that match context CAD
    todo: use pynini
    """
    x = x.split(' ')
    A, B, C, D = \
        R.A, R.B, R.C, R.D
    n_A, n_C, n_D, n_x = \
        len(A), len(C), len(D), len(x)

    # Find offsets in x that match A
    offsets = [i for i in range(n_x) if match_rule(A, x, i, 'LR->')]

    # Find pre-offsets in x that match C
    offsets = [i for i in offsets if match_rule(C, x, i - 1, '<-RL')]

    # Find post-offsets in x that match D
    offsets = [i for i in offsets if match_rule(D, x, i + n_A, 'LR->')]

    # Apply at each offset
    products = []
    for i in offsets:
        x_A = x[i:(i + n_A)]
        x_prefix = x[:i]
        x_suffix = x[(i + n_A + 1):]
        y = x_prefix + replace_rule(B, x_A) + x_suffix
        products.append(y)

    apply_flag = len(offsets) > 0
    return products, apply_flag


def match_rule(A, x, x_offset, direction='LR->'):
    """
    Attempt to match part of a FtrRule (left-context | focus | right-context)  against a segment sequence, starting at offset position in the sequence
    todo: use pynini
    """
    assert ((direction == 'LR->') or (direction == '<-RL'))
    n_A = len(A)
    n_x = len(x)
    if direction == 'LR->':
        for i in range(n_A):
            if A[i] == 'X':  # Sigma*
                return True
            if (x_offset + i) >= n_x:  # Off right edge of x
                return False
            if not match_ftrs(A[i], x[x_offset + i]):  # Mismatch
                return False
        return True
    elif direction == '<-RL':
        for i in range(n_A):
            if A[(n_A - 1) - i] == 'X':  # Sigma*
                return True
            if (x_offset - i) < 0:  # Off left edge of x
                return False
            if not match_ftrs(A[(n_A - 1) - i], x[x_offset - i]):  # Mismatch
                return False
        return True
    return None


def replace_rule(B, x_A):
    """
    Apply change A -> B to portion of segment sequence that matches rule focus
    todo: use pynini
    """
    return B  # xxx fixme
