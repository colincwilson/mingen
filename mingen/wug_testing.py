import sys
import numpy as np

import config
from rules import *
from phtrs import str_util
import pynini_util


def wug_test(wugs, rules, score_type='confidence', mode='rate'):
    """
    Assign ratings to input/output forms (mode='rate', default), 
    or generate output forms with ratings from inputs (mode='generate'),
    for a list of wug items.
    """
    print('Wug testing ...')
    # Symbol environment.
    syms = [x for x in config.sym2ftrs]
    sigstar, symtable = pynini_util.sigstar(syms)

    stems = [str(x) for x in wugs['stem']]
    if mode == 'rating':
        outputs = [str(x) for x in wugs['output']]
    else:
        outputs = [''] * len(stems)  # todo: remove
    wordforms = list(zip(stems, outputs))

    R = [FtrRule.from_str(rule) for rule in rules['rule']]
    R = [(rule, score, idx) for (rule, score, idx) \
        in zip(R, rules[score_type], rules['rule_idx'])]

    max_rating = {}
    max_rule = {}
    print('iter')
    for i, rule_ in enumerate(R):
        if i % 500 == 0:
            print(i)

        # Convert rule to segment regexes.
        rule, score, rule_idx = rule_
        (A, B, C, D) = rule.regexes()

        # Subset of wug data s.t. CAD occurs in input.
        CAD = [Z for Z in [C, A, D] if Z != '∅']
        CAD = ' '.join(CAD)
        if CAD != '':
            subdat = [wf for wf in wordforms if re.search(CAD, wf[0])]
        else:
            subdat = wordforms
        if len(subdat) == 0:
            continue

        # Compile rule to FST.
        rule_fst = pynini_util.compile_rule(A, B, C, D, sigstar, symtable)

        for (stem, output) in subdat:
            if mode == 'rate':
                rewrite_val = pynini_util.rewrites( \
                    rule_fst, stem, output, sigstar, symtable)
                if not rewrite_val['hit']:
                    continue
                if (stem, output) not in max_rating \
                    or score > max_rating[(stem, output)]:
                    max_rating[(stem, output)] = score
                    max_rule[(stem, output)] = rule_
            if mode == 'generate':
                pred = pynini_util.rewrite( \
                    rule_fst, stem, sigstar, symtable)
                if pred is None:  # Out-of-scope.
                    continue
                if (stem, pred) not in max_rating \
                    or score > max_rating[(stem, pred)]:
                    max_rating[(stem, pred)] = score
                    max_rule[(stem, pred)] = rule_

    # Results
    print()
    wug_results = []
    for forms, rating in max_rating.items():
        stem, output = forms
        rule, score, rule_idx = max_rule[(stem, output)]
        print(stem, output, rating)
        print(rule)
        print()
        wug_results.append((stem, output, rating, rule_idx))
    return wug_results
