# -*- coding: utf-8 -*-

import re
import pandas as pd

import config
from rules import *
import mingen
import reliability


def main():
    # Global config
    # todo: move to yaml / configargparse
    verbosity = 10

    # Phonological features
    config.begin_delim = '⋊'
    config.end_delim = '⋉'
    config.zero = '∅'
    phon_ftrs = pd.read_csv(
        '/Users/colin/Code/Python/tensormorph_data/unimorph/eng.ftr',
        sep='\t',
        header=0)
    phon_ftrs.columns.values[0] = 'seg'
    config.segs = segs = phon_ftrs['seg']
    phon_ftrs = phon_ftrs.drop('seg', 1)  # Segment column, not a feature
    phon_ftrs = phon_ftrs.drop('sym', 1)  # Redundant with X = (Sigma*)
    config.phon_ftrs = phon_ftrs
    config.ftr_names = [x for x in phon_ftrs.columns.values]
    if verbosity > 5:
        print(config.ftr_names)
        print(config.phon_ftrs)

    # Map from segments to feature-value dictionaries and feature matrices
    seg2ftrs = {}
    for i, seg in enumerate(segs):
        ftrs = phon_ftrs.iloc[i, :].to_dict()
        seg2ftrs[seg] = ftrs
    seg2ftrs_ = {}  # Vectorized feature matrices
    for seg, ftrs in seg2ftrs.items():
        seg2ftrs_[seg] = tuple([val for key, val in ftrs.items()])
    config.seg2ftrs = seg2ftrs
    config.seg2ftrs_ = seg2ftrs_
    if verbosity > 5:
        for seg in seg2ftrs:
            print(seg)
            print(seg2ftrs[seg])
            print(seg2ftrs_[seg])
            print()

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

    # Training data
    dat = pd.read_csv(
        '/Users/colin/Code/Python/tensormorph_data/unimorph/eng_all_past',
        sep='\t',
        names=['wordform1', 'wordform2', 'morphosyn'])
    dat = dat.drop_duplicates().reset_index()
    dat = dat.sample(n=200)  # xxx subset for debugging
    dat['wordform1'] = fix_transcription(dat['wordform1'], config.seg_fixes)
    dat['wordform2'] = fix_transcription(dat['wordform2'], config.seg_fixes)
    dat['wordform1'] = [add_delim(x) for x in dat['wordform1']]
    dat['wordform2'] = [add_delim(x) for x in dat['wordform2']]
    config.dat_train = dat_train = dat
    print(config.dat_train)

    # Make word-specific (base) rules, apply recursive minimal generalization,
    # and compute rule accuracies
    make_rules = True
    score_rules = True
    if make_rules:
        R_base = [base_rule(w1, w2) for (w1, w2) \
            in zip(dat_train['wordform1'], dat_train['wordform2'])]
        R_ftr = [featurize_rule(R) for R in R_base]

        R_all = mingen.generalize_rules_rec(R_ftr)
        print(f'number of rules: {len(R_all)}')

        rules = pd.DataFrame({'rule': [str(R) for R in R_all]})
        rules['rule_len'] = [len(x) for x in rules['rule']]
        rules.to_csv('rules_out.tsv', index=False, sep='\t')

    # Compute scope and hits for each rule
    if score_rules:
        rules = pd.read_csv('rules_out.tsv', sep='\t')
        #rules = rules.head(n=10)  # xxx subset for debugging
        R_all = [str2ftr_rule(R) for R in rules['rule']]

        # Score rules
        hits_all, scopes_all = reliability.score_rules(R_all)
        rules['hits'] = hits_all
        rules['scope'] = scopes_all
        rules.to_csv('rules_scored.tsv', sep='\t', index=False)


if __name__ == "__main__":
    main()