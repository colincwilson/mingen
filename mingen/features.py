# -*- coding: utf-8 -*-

import re
import config


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
        if (F1[i] == '0') or (F2[i] == '0'):
            continue
        if F1[i] == F2[i]:
            F[i] = F1[i]
            any_match = True
    return tuple(F), any_match


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


def ftrs2str(F):
    """ String corresponding to sequence of feature matrices"""
    return ' '.join([ftrs2str1(Fi) for Fi in F])


def ftrs2str1(F):
    """ String corresponding to feature matrix, with non-zero values only """
    if F == 'X':
        return 'X'
    ftr_names = config.ftr_names
    #ftrvals = [f'{val}{ftr}' for ftr, val in F.items() if val != '0']
    ftrvals = [f"{F[i]}{ftr_names[i]}" \
                for i in range(len(F)) if F[i] != '0']
    return '[' + ', '.join(ftrvals) + ']'


def str2ftrs(x):
    """ String to sequence of feature matrices (inverse of ftrs2str) """
    y = x.split(' [')
    y = [str2ftrs1(yi) for yi in y]
    return tuple(y)


def str2ftrs1(x):
    """ String to feature matrix (inverse of ftrs2str1) """
    if x == 'X':
        return 'X'
    y = re.sub('\\]', '', x)
    y = y.split(', ')
    print(y)
    ftrs = ['0'] * len(config.ftr_names)
    for spec in y:
        val = spec[0]
        ftr = spec[1:]
        print(val, ftr)
        try:
            ftrs[config.ftr_names.index(ftr)] = val
        except:
            print(val, ftr)
    sys.exit(0)
    return tuple(ftrs)