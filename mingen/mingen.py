# -*- coding: utf-8 -*-

import re, sys
from collections import namedtuple
import pandas as pd
import config

# TODO: accuracy, phonology, etc.


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
        parts2 = {X: ftrs2print(parts2[X]) for X in parts2}

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


def add_delim(x):
    """
    Add begin/end delimiters to space-separated segment strings
    """
    y = f'{config.begin_delim} {x} {config.end_delim}'
    return y


def fix_transcription(x, seg_fixes):
    """
    Fix transcription of list of space-separated segment strings by applying substitutions
    """
    y = x
    for (s, r) in seg_fixes.items():
        y = [re.sub(s, r, yi) for yi in y]
    return y


def ftrs2regex(F):
    """ Segment regex for sequence of feature matrices """
    return ' '.join([ftrs2regex1(Fi) for Fi in F])


def ftrs2regex1(F):
    """ Segment regex for single feature matrix """
    if F == 'X':
        return 'X'
    segs = [seg for seg in config.seg2ftrs \
            if match_ftrs(F, seg)]
    return '(' + '|'.join(segs) + ')'


def ftrs2print(F):
    """ String corresponding to sequence of feature matrices"""
    return ' '.join([ftrs2print1(Fi) for Fi in F])


def ftrs2print1(F):
    """ String corresponding to feature matrix, with non-zero values only """
    if F == 'X':
        return 'X'
    ftr_names = config.ftr_names
    #ftrvals = [f'{val}{ftr}' for ftr, val in F.items() if val != '0']
    ftrvals = [f"{F[i]}{ftr_names[i]}" \
                for i in range(len(F)) if F[i] != '0']
    return '[' + ', '.join(ftrvals) + ']'


def lcp(x, y, direction='LR->'):
    """
    Longest common prefix (or suffix) of two segment sequences
    """
    assert ((direction == 'LR->') or (direction == '<-RL'))
    if direction == '<-RL':
        x = x[::-1]
        y = y[::-1]
    n_x, n_y = len(x), len(y)
    n = max(n_x, n_y)
    for i in range(n + 1):
        if i >= n_x:
            match = x
            break
        if i >= n_y:
            match = y
            break
        if x[i] != y[i]:
            match = x[:i]
            break
    if direction == '<-RL':
        match = match[::-1]
    return match


def make_base_rule(x, y):
    """
    Create SegRule A -> B / C __D by aligning two segment sequences
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
    return SegRule(tuple(A), tuple(B), tuple(C), tuple(D))


def featurize_rule(R):
    """
    Convert SegRule to FtrRule by replacing segments in context with feature matrices
    """
    C = [config.seg2ftrs_[seg] for seg in R.C]
    D = [config.seg2ftrs_[seg] for seg in R.D]
    return FtrRule(R.A, R.B, tuple(C), tuple(D))


def generalize_context(X1, X2, direction='LR->'):
    """
    Apply minimal generalization to pair of FtrRule contexts
    """
    assert ((direction == 'LR->') or (direction == '<-RL'))
    n_X1 = len(X1)
    n_X2 = len(X2)
    n_min = min(n_X1, n_X2)
    n_max = max(n_X1, n_X2)
    if direction == '<-RL':
        X1 = X1[::-1]
        X2 = X2[::-1]

    Y = []
    seg_ident_flag = True
    for i in range(n_max):
        # X (= Sigma*) and terminate if have exceeded shorter context
        # or have already unified features
        if (i >= n_min) or (not seg_ident_flag):
            Y.append('X')
            break
        # X (Sigma*) and terminate if either is X
        if (X1[i] == 'X') or (X2[i] == 'X'):
            Y.append('X')
            break
        # Match segments perfectly
        # (NB. Conforms to A&H spec only if at least one
        # of the rules has contexts specified with segments)
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
    if C is None or D is None:
        return None

    R = FtrRule(R1.A, R1.B, C, D)
    return R


def generalize_rules_rec(Rs):
    """
    Recursively apply minimal generalization to set of FtrRules
    """
    # (invariant) Rules grouped by common change
    # Word-specific rules
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

    # First-step minimal generalization
    print('First-step mingen ...')
    R_new = {}
    for change, rules_base in R_base.items():
        print(f'\t{change} [{len(rules_base)}]')
        rules_base = [R for R in rules_base]
        rules_new = set()
        n = len(rules_base)
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

    # xxx organize rules by C and D within change
    #for change, rules_all in R_new.items():
    #    for R in rules_all:
    #        print(repr(R))
    #sys.exit(0)

    # Recursive minimal generalization
    for i in range(10):  # xxx loop forever
        # Report number of rules by change
        print(f"iteration {i}")

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

    # Write rules
    rules_out = [str(R) for change, rules in R_all.items() \
                    for R in rules]
    rules_out = pd.DataFrame(rules_out, columns=['rule'])
    rules_out['rule_len'] = [len(x) for x in rules_out['rule']]
    rules_out.to_csv('rules_out.tsv', index=False, sep='\t')

    return R_all


def match_ftrs_(F, seg):
    """
    Test whether feature matrix subsumes segment features
    [Args: feature dicts]
    """
    seg_ftrs = config.seg2ftrs[seg]
    for (ftr, val) in F.items():
        if seg_ftrs[ftr] != val:
            return False
    return True


def match_ftrs(F, seg):
    """
    Test whether feature matrix subsumes segment features
    [Args: feature vectors]
    """
    seg_ftrs = config.seg2ftrs_[seg]
    n = len(seg_ftrs)
    for i in range(n):
        if F[i] == '0':
            continue
        if seg_ftrs[i] != F[i]:
            return False
    return True


def unify_ftrs_(F1, F2):
    """
    Retain common values from two feature matrices
    [Args: feature dicts]
    """
    # Unify(Sigma*,F2) = unify(F1,Sigma*) = Sigma*
    if (F1 == 'X') or (F2 == 'X'):
        return 'X'
    # Ordinary unification
    # todo: built-in dictionary function?
    F = {}
    for (ftr, val) in F1.items():
        if (ftr in F2) and (F2[ftr] == val):
            F[ftr] = val
    return F


def unify_ftrs(F1, F2):
    """
    Retain common values from two feature matrices
    [Args: feature vectors]
    """
    if (F1 == 'X') or (F2 == 'X'):
        return 'X'
    n = len(F1)
    F = ['0'] * n
    any_match = False
    for i in range(n):
        if F1[i] == '0':
            continue
        if F1[i] == F2[i]:
            F[i] = F1[i]
            any_match = True
    return tuple(F), any_match


def match_rule(A, x, x_offset, direction='LR->'):
    """
    Attempt to match part of a rule (left-context | focus | right-context)  against a segment sequence, starting at offset position in the sequence
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


def apply_rule(R, x):
    """
    Apply rule A -> B / C __ D at all positions in segment sequence that match context CAD
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


def main():
    # Global config todo: move to yaml / configargparse
    # Phonological features
    config.begin_delim = '⋊'
    config.end_delim = '⋉'
    phon_ftrs = pd.read_csv(
        '/Users/colin/Code/Python/tensormorph_data/unimorph/eng.ftr',
        sep='\t',
        header=0)
    phon_ftrs.columns.values[0] = 'seg'
    seg2ftrs = {}
    seg2ftrs_ = {}
    for i, seg in enumerate(phon_ftrs['seg']):
        ftrs = phon_ftrs.iloc[i, :].iloc[1:].to_dict()
        seg2ftrs[seg] = ftrs
        seg2ftrs_[seg] = tuple([val for key, val in ftrs.items()])
    config.phon_ftrs = phon_ftrs
    config.ftr_names = phon_ftrs.columns.values[1:]
    config.seg2ftrs = seg2ftrs
    config.seg2ftrs_ = seg2ftrs_
    print(seg2ftrs_)
    print(config.ftr_names)
    print(config.phon_ftrs)

    # Segment transcription fixes
    config.seg_fixes = {  # English
        'eɪ': 'e',
        'oʊ': 'o',
        'əʊ': 'o',
        'aɪ': 'a ɪ',
        'aʊ': 'a ʊ',
        'ɔɪ': 'ɔ ɪ',
        'ɝ': 'ɛ ɹ',
        'ˠ': '',
        'm̩': 'm',
        'n̩': 'n',
        'l̩': 'l',
        'ɜ': 'ə',
        'uːɪ': 'uː ɪ',
        'ɔ̃': 'ɔ',
        'ː': '',
        'r': 'ɹ',
    }

    # Input/output training data
    dat = pd.read_csv(
        '/Users/colin/Code/Python/tensormorph_data/unimorph/eng_all_past',
        sep='\t',
        names=['wordform1', 'wordform2', 'morphosyn'])
    dat = dat.drop_duplicates().reset_index()
    #dat = dat.head(n=200)  # xxx subset for debugging
    dat['wordform1'] = fix_transcription(dat['wordform1'], config.seg_fixes)
    dat['wordform2'] = fix_transcription(dat['wordform2'], config.seg_fixes)
    dat['wordform1'] = [add_delim(x) for x in dat['wordform1']]
    dat['wordform2'] = [add_delim(x) for x in dat['wordform2']]
    config.dat_train = dat_train = dat
    print(config.dat_train)
    print(len(dat_train))

    # Base rules, convert to features
    R_base = [make_base_rule(w1, w2) \
        for (w1, w2) in zip(dat_train['wordform1'], dat_train['wordform2']) ]
    print(R_base[0])
    print(R_base[1])
    R_ftr = [featurize_rule(R) for R in R_base]
    #print(R_ftr[0])
    #print(R_ftr[1])

    # Minimal generalization of epenthesis rules
    R_epen = [R for R in R_ftr \
                if ' '.join(R.A) == '' and ' '.join(R.B) == 'ɪ d']
    R_gen = R_epen[0]
    for i in range(1, len(R_epen)):
        R_gen = generalize_rules(R_gen, R_epen[i])
        #print(R_gen)
    #print(R_gen)

    # Recursive minimal generalization of all rules
    generalize_rules_rec(R_ftr)


if __name__ == "__main__":
    main()