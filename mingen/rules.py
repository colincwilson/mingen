# -*- coding: utf-8 -*-

import config
from str_util import *
from features import *


class SegRule():
    """ Rule stated over segments """

    def __init__(self, A, B, C, D):
        self.A = A
        self.B = B
        self.C = C
        self.D = D

    def __str__(self):
        A_ = ' '.join(self.A) if self.A != '' else config.zero
        B_ = ' '.join(self.B) if self.B != '' else config.zero
        C_ = ' '.join(self.C) if self.C != '' else config.zero
        D_ = ' '.join(self.D) if self.D != '' else config.zero
        return f'{A_} -> {B_} / {C_} __ {D_}'


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
        if len(D) == 0:
            print('error creating feature rule from')
            print(A, B, C, D)
            sys.exit(0)
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
        """ String with feature matrices and X (for the humans) """
        if hasattr(self, '_str'):
            return self._str
        A_ = ' '.join(self.A) if self.A != '' else config.zero
        B_ = ' '.join(self.B) if self.B != '' else config.zero
        C_ = ftrs2str(self.C)
        D_ = ftrs2str(self.D)
        if C_ == '' or D_ == '':
            print('empty string (expected feature matrix)')
            print('C:', self.C)
            print('C_:', C_)
            print('D:', self.D)
            print('D_:', D_)
            sys.exit(0)
        return f'{A_} -> {B_} / {C_} __ {D_}'

    def __repr__(self):
        """ String with segment regexs (for compilation to FST) """
        if hasattr(self, '_repr'):
            return self._repr
        A_ = ' '.join(self.A)
        B_ = ' '.join(self.B)
        C_ = ftrs2regex(self.C)
        D_ = ftrs2regex(self.D)
        return f'{A_} -> {B_} / {C_} __ {D_}'


def base_rule(x: str, y: str) -> SegRule:
    """
    Create rule A -> B / C __D by aligning input x with output y
    """
    x = x.split(' ')
    y = y.split(' ')
    # Left-hand context
    C = lcp(x, y, 'LR->')
    # Right-hand context
    x = x[len(C):]
    y = y[len(C):]
    D = lcp(x, y, '<-RL')
    # Change
    A = x[:-len(D)]
    B = y[:-len(D)]

    # Zeros in change
    A = config.zero if len(A) == 0 else A
    B = config.zero if len(B) == 0 else B

    # Identity rule xxx change locn at end
    if (A == config.zero) and (B == config.zero):
        C = C[:-1]  # Remove end_delim
        D = [config.end_delim]

    rule = SegRule(tuple(A), tuple(B), tuple(C), tuple(D))
    return rule


def featurize_rule(R: SegRule) -> FtrRule:
    """
    Convert SegRule to FtrRule by replacing segments in context with feature matrices
    """
    A = R.A
    B = R.B
    C = [config.seg2ftrs_[seg] for seg in R.C]
    D = [config.seg2ftrs_[seg] for seg in R.D]
    return FtrRule(A, B, tuple(C), tuple(D))


def str2ftr_rule(x: str) -> FtrRule:
    """
    Create FtrRule from string A -> B / C __ D 
    with contexts defined by feature matrices
    (inverse of FtrRule.__str__)
    """
    AB, CD = x.split(' / ')
    A, B = AB.split(' -> ')
    C, D = CD.split(' __ ')
    A = tuple(A.split(' '))
    B = tuple(B.split(' '))
    C = str2ftrs(C)
    D = str2ftrs(D)
    R = FtrRule(A, B, C, D)
    return R
