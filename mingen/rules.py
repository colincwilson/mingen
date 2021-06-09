# -*- coding: utf-8 -*-

import config
from str_util import *
from features import *


class SegRule():
    """ Rule stated over segments """

    def __init__(self, A, B, C, D):
        """ Construct from segment tuples (see base_rule()) """
        self.A = A
        self.B = B
        self.C = C
        self.D = D

    def __str__(self):
        if self.A == '' or self.B == '' or self.C == '' or self.D == '':
            print(f'Empty rule part: {A}, {B}, {C}, {D}')
            sys.exit(0)
        A_, B_, C_, D_ = map(lambda X: ' '.join(X),
                             [self.A, self.B, self.C, self.D])
        return f'{A_} -> {B_} / {C_} __ {D_}'


class FtrRule():
    """
    Rule with contexts defined by features and X (Sigma*)
    """

    def __init__(self, A, B, C, D):
        """ Construct from change stated over segments and context stated over features (see from_segrule())"""
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
        """ String with feature matrices and X (for the humans) """
        A_, B_ = map(lambda Z: ' '.join(Z), [self.A, self.B])
        C_, D_ = map(lambda Z: ftrs2str(Z), [self.C, self.D])
        if C_ == '' or D_ == '':
            print('Empty string (expected feature matrix)')
            print('C:', self.C)
            print('C_:', C_)
            print('D:', self.D)
            print('D_:', D_)
            sys.exit(0)
        return f'{A_} -> {B_} / {C_} __ {D_}'

    def __repr__(self):
        """ String with segment regexs (for compilation to FST) """
        A_, B_ = map(lambda Z: ' '.join(Z), [self.A, self.B])
        C_, D_ = map(lambda Z: ftrs2regex(Z), [self.C, self.D])
        return f'{A_} -> {B_} / {C_} __ {D_}'

    def regexes(self):
        """ Separate regular expressions for change and context """
        R_regex = repr(self)
        AB, CD = R_regex.split(' / ')
        A, B = AB.split(' -> ')
        C, D = CD.split(' __ ')
        return (A, B, C, D)

    @classmethod
    def from_segrule(cls, R: SegRule):
        """
        Convert SegRule to FtrRule by replacing segments in context with feature matrices
        """
        A = R.A
        B = R.B
        C = [config.seg2ftrs_[seg] for seg in R.C]
        D = [config.seg2ftrs_[seg] for seg in R.D]
        return FtrRule(A, B, tuple(C), tuple(D))

    @classmethod
    def from_str(cls, x: str):
        """
        FtrRule from string A -> B / C __ D 
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
        return FtrRule(A, B, C, D)


def base_rule(inpt: str, outpt: str) -> SegRule:
    """
    Learn word-specific rule A -> B / C __D by aligning input and output
    """
    inpt = inpt.split(' ')
    outpt = outpt.split(' ')
    # Left-hand context
    C = lcp(inpt, outpt, prefix=True)
    # Right-hand context
    inpt = inpt[len(C):]
    outpt = outpt[len(C):]
    D = lcp(inpt, outpt, prefix=False)
    # Change
    A = inpt[:-len(D)]
    B = outpt[:-len(D)]

    # Zeros in change
    A = config.zero if len(A) == 0 else A
    B = config.zero if len(B) == 0 else B

    # Identity rule xxx change locn at end
    if (A == config.zero) and (B == config.zero):
        C = C[:-1]  # Remove eos from left-hand side
        D = [config.eos]  # Add eos to right_hand side

    rule = SegRule(tuple(A), tuple(B), tuple(C), tuple(D))
    return rule
