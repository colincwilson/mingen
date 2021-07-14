# -*- coding: utf-8 -*-

import re, sys
import pandas as pd
#import edlib
import config
from rules import *
import pynini_util


def generate_wugs(rules):
    # Symbol environment
    syms = [x for x in config.sym2ftrs]
    sigstar, symtable = pynini_util.sigstar(syms)

    # Monosyllabic items in training data
    vowels = '[ɑaʌɔoəeɛuʊiɪ]'
    monosyll_regex = \
        '⋊ ([^ɑaʌɔoəeɛuʊiɪ]+ )([ɑaʌɔoəeɛuʊiɪ] )+([^ɑaʌɔoəeɛuʊiɪ]+ )*⋉'
    lex = config.dat_train
    monosyll = lex[(lex['stem'].str.match(monosyll_regex))]
    print(f'{len(monosyll)} monosyllables')

    # Attested onsets and rimes of monosyllables
    onsets = [re.sub('[ɑaʌɔoəeɛuʊiɪ].*', '', x) for x in monosyll['stem']]
    rimes = [
        re.sub('.*?([ɑaʌɔoəeɛuʊiɪ].*)', '\\1', x) for x in monosyll['stem']
    ]
    onsets = set([x.strip() for x in onsets])
    rimes = set([x.strip() for x in rimes])
    onset_fst = pynini_util.union( \
        pynini_util.accep([x for x in onsets], symtable))
    rime_fst = pynini_util.union( \
        pynini_util.accep([x for x in rimes], symtable))
    phonotactics = onset_fst + rime_fst
    phonotactics = phonotactics.optimize()
    print(f'{len(onsets)} onsets')
    print(f'{len(rimes)} rimes')

    # Irregular rules
    #change = 'ɪ -> ʌ'
    #change = 'a ɪ -> o'
    #change = 'i -> ɛ'
    #change = 'ɪ -> ɑ'
    #change = 'e -> o'
    #change = 'e -> ʊ'
    change = 'i p -> ɛ p t'
    A, B = change.split(' -> ')  # xxx handle zeros
    rules = rules[(rules['rule'].str.contains(f'^{change} /'))]
    rules = rules \
            .sort_values('confidence', ascending=False) \
            .reset_index(drop = True)
    R = [FtrRule.from_str(rule) for rule in rules['rule']]
    R = [rule.regexes() for rule in R]
    print(f'change: {change}')
    print(f'{len(rules)} rules')

    # Real stems that undergo rules
    stems_A = monosyll[(monosyll['stem'].str.contains(A))] \
            .reset_index(drop=True)
    stems_apply = []
    for i, stem in enumerate(stems_A['stem']):
        outpt = stems_A['output'][i]
        for j, rule in enumerate(R):
            A, B, C, D = rule
            CAD = [Z for Z in [C, A, D] if Z != '']
            CAD = ' '.join(CAD)
            if not re.search(CAD, stem):
                continue
            val = pynini_util.rewrites(rule, stem, outpt, sigstar, symtable)
            val['stem'] = stem
            val['output'] = outpt
            val['model_rating'] = rules['confidence'][j]
            #val = {
            #    'stem': stem,
            #    'output': outpt,
            #    'model_rating':
            #} | val
            stems_apply.append(val)
            #print(val)
            break
    stems_apply = pd.DataFrame(stems_apply)
    stems_hit = stems_apply[(stems_apply['hit'] == 1)] \
                  .sort_values('model_rating', ascending=False) \
                  .reset_index(drop=True)
    print(f'{len(stems_hit)} existing stems:')
    print(stems_hit)
    print(print([stem for stem in stems_hit['stem']]))

    # Rimes of real stems that undergo rules
    rimes_hit = [re.sub('.*?([ɑaʌɔoəeɛuʊiɪ].*)', '\\1', x) \
        for x in stems_hit['stem']]
    rimes_hit = set([x.strip() for x in rimes_hit])
    rime_hit_fst = pynini_util.union( \
        pynini_util.accep([x for x in rimes_hit], symtable))
    phonotactics_hit = onset_fst + rime_hit_fst
    phonotactics_hit = phonotactics_hit.optimize()

    # Wug stems one-edit away from real stems
    stem_fst = pynini_util.accep([stem for stem in stems_apply['stem']],
                                 symtable)
    stem_fst = pynini_util.union(stem_fst)
    edit1_fst = pynini_util.edit1_fst(sigstar, symtable)
    wug_fst = stem_fst @ edit1_fst
    #wug_fst @= phonotactics  # Filter by general phonotactics
    wug_fst @= phonotactics_hit  # Filter by rimes of real hit stems
    wugs = pynini_util.ostrings(wug_fst, symtable)
    sorted(wugs)
    wugs = set(wugs)
    print(f'{len(wugs)} potential wugs')

    # Wug stems within/beyond scope of rules
    wugs_apply = []
    wugs_A = [wug for wug in wugs if re.search(A, wug)]
    for wug in wugs_A:
        rewrite_val = None
        for j, rule in enumerate(R):
            A, B, C, D = rule
            CAD = [Z for Z in [C, A, D] if Z != '']
            CAD = ' '.join(CAD)
            if not re.search(CAD, wug):
                continue
            rewrite_val = pynini_util.rewrites(rule, wug, '', sigstar, symtable)
            rewrite_val['stem'] = wug
            rewrite_val['output'] = None
            rewrite_val['model_rating'] = rules['confidence'][j]
            #rewrite_val = {
            #    'stem': wug,
            #    'output': None,
            #    'model_rating': rules['confidence'][j]
            #} | rewrite_val
            break
        if rewrite_val is None:
            rewrite_val = {
                'stem': wug,
                'output': None,
                'model_rating': 0,
                'in_scope': 0,
                'hit': 0
            }
        wugs_apply.append(rewrite_val)

    # Report wugs
    wugs_apply = pd.DataFrame(wugs_apply)
    wugs_apply = wugs_apply[~(wugs_apply.stem.isin(lex['stem']))] \
                 .reset_index(drop = True)
    wugs_in = wugs_apply[(wugs_apply['in_scope'] == 1)] \
                .sort_values('model_rating', ascending=False)
    wugs_out = wugs_apply[(wugs_apply['in_scope'] == 0)] \
                .sort_values('stem')
    print(f'wugs in scope ({len(wugs_in)}):\n{wugs_in.head(40)}')
    print([wug for wug in wugs_in['stem']])
    print(f'wug near-misses ({len(wugs_out)}):\n{wugs_out}')
    print([wug for wug in wugs_out['stem']])

    return wugs_in, wugs_out