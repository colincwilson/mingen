# -*- coding: utf-8 -*-

import re, sys
import edlib
import config
from rules import *


def generate(rules):
    # Rules that make target change
    #change = 'ɪ -> ɑ'
    change = 'i -> ɛ'
    focus, outcome = change.split(' -> ')
    rules = rules[(rules['rule'].str.contains(f'^{change} /'))]
    Rs = [FtrRule.from_str(R) for R in rules['rule']]
    Rs = [R.regexes() for R in Rs]
    print(f'{len(rules)} rules')

    # Monosyllabic items in training data
    vowels = '[ɑaʌɔoəeɛuʊiɪ]'
    monosyll_regex = '⋊ ([^ɑaʌɔoəeɛuʊiɪ]+ )([ɑaʌɔoəeɛuʊiɪ] )+([^ɑaʌɔoəeɛuʊiɪ]+ )*⋉'
    lex = config.dat_train
    monosyll = lex[(lex['stem'].str.match(monosyll_regex))]

    # Attested pre-V and post-V strings in monosyllables
    prefixes = [re.sub('[ɑaʌɔoəeɛuʊiɪ].*$', '', x) for x in monosyll['stem']]
    suffixes = [re.sub('^.*[ɑaʌɔoəeɛuʊiɪ]', '', x) for x in monosyll['stem']]
    prefixes = [p.strip() for p in prefixes]
    suffixes = [s.strip() for s in suffixes]
    #print(f'{len(monosyll)} seed lexical items')
    #print(prefixes)

    # Attested pre-V strings that match at least one left-hand context,
    # attested post-V strings that match at least one right-hand context
    prefixes_in = []
    suffixes_in = []
    for i in range(len(prefixes)):
        p = prefixes[i]
        s = suffixes[i]
        prefix_in = False
        suffix_in = False
        for R in Rs:
            A, B, C, D = R
            #print(C, D)
            if not prefix_in and re.search(C + '$', p):
                prefixes_in.append(p)
                prefix_in = True
            if not suffix_in and re.search('^' + D, s):
                suffixes_in.append(s)
                suffix_in = True
            if prefix_in and suffix_in:
                break
    #print(len(prefixes_in))
    #print(len(suffixes_in))

    # Attested pre-V strings that do not match any left-hand context,
    # attested post-V strings that do not match any right-hand context
    prefixes_in = set(prefixes_in)
    suffixes_in = set(suffixes_in)
    prefixes_out = set(prefixes) - prefixes_in
    suffixes_out = set(suffixes) - suffixes_in
    #print(prefixes_out, len(prefixes_out))
    #print(suffixes_out, len(suffixes_out))

    # Potential wug items outside the scope of target rules, created by
    # recombining attested pre-V + focus + post-V
    wugs_prefix_out = [' '.join([p, focus, s]) \
        for p in prefixes_out for s in suffixes_in]
    wugs_suffix_out = [' '.join([p, focus, s]) \
        for p in prefixes_in for s in suffixes_out]
    #print(wugs1)

    # Potential wug items that are one edit away from example
    #ex = '⋊ s ɪ ŋ ⋉'
    #ex = '⋊ ɹ ɪ ŋ ⋉'
    #ex = '⋊ b ɹ ɪ ŋ ⋉'
    #ex = '⋊ s p l ɪ ŋ ⋉'
    #ex = '⋊ s w ɪ ŋ ⋉'
    ex = '⋊ b l i d ⋉'
    ex = ex.split(' ')
    for wugs_out in [wugs_prefix_out, wugs_suffix_out]:
        for wug in wugs_out:
            wug = wug.split(' ')
            d = edlib.align(ex, wug, task='distance')
            d = d['editDistance']
            if d < 2:
                print(' '.join(ex), '\t', ' '.join(wug), '\t', d)
        print('-----')
