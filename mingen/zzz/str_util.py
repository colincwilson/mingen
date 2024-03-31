# -*- coding: utf-8 -*-

# Compute longest common prefix/suffix of pair of strings, handle delimiters and markers, fix transcriptions

import re
import config


def lcp(x, y, prefix=True):
    """
    Longest common prefix (or suffix) of two segment sequences
    """
    if not prefix:
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
    if not prefix:
        match = match[::-1]
    return match


def add_delim(x):
    """
    Add begin/end delimiters to space-separated segment string
    """
    y = f'{config.bos} {x} {config.eos}'
    return y


def delete_markers(x):
    """
    Remove markers indicating loci of rule application from space-separated string
    """
    y = x
    y = re.sub('⟨ ', '', y)
    y = re.sub(' ⟩', '', y)
    return y


def fix_transcription(x, seg_fixes):
    """
    Fix transcription of space-separated segment strings by applying substitutions
    """
    y = x
    for (s, r) in seg_fixes.items():
        y = [re.sub(s, r, yi) for yi in y]
    return y
