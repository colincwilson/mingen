# -*- coding: utf-8 -*-

import re
import pandas as pd

import config
from rules import *
from mingen import *
from accuracy import *


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
        ftrs = phon_ftrs.iloc[i, :].iloc[2:].to_dict()
        seg2ftrs[seg] = ftrs
        seg2ftrs_[seg] = tuple([val for key, val in ftrs.items()])
    config.phon_ftrs = phon_ftrs
    config.ftr_names = [x for x in phon_ftrs.columns.values[1:]]
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

    # Recursive minimal generalization of base rules,
    # or read rules from file
    make_rules = False
    if make_rules:
        R_base = [make_base_rule(w1, w2) for (w1, w2) \
            in zip(dat_train['wordform1'], dat_train['wordform2'])]
        R_ftr = [featurize_rule(R) for R in R_base]
        R_all = generalize_rules_rec(R_ftr)
    else:
        rules = pd.read_csv('rules_out.tsv', sep='\t')
        #rules = rules.head(n=10)  # xxx subset for debugging
        R_all = [str2rule(R) for R in rules['rule']]

        # Score rules
        hits, scopes = score_rules(R_all)
        rules['hits'] = hits
        rules['scopes'] = scopes
        rules.to_csv('rules_scored.tsv', sep='\t', index=False)


if __name__ == "__main__":
    main()