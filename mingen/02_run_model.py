# -*- coding: utf-8 -*-

import pickle, sys
import pandas as pd

import config
from rules import *
import mingen
import reliability as reliability
import wug_test


def main():
    make_rules = 1
    score_rules = 1
    evaluate_wugs = 1

    # Import config (as created by 01_prepare_data)
    LANGUAGE = ['eng', 'deu', 'nld', 'tiny'][0]
    config_save = pickle.load(open(f'../data/{LANGUAGE}_config.pkl', 'rb'))
    for key, val in config_save.items():
        setattr(config, key, val)

    # Make word-specific (base) rules, apply recursive minimal generalization
    if make_rules:
        dat_train = config.dat_train
        R_base = [base_rule(w1, w2) for (w1, w2) \
            in zip(dat_train['stem'], dat_train['output'])]
        R_ftr = [featurize_rule(R) for R in R_base]

        R_all = mingen.generalize_rules_rec(R_ftr)
        print(f'number of rules: {len(R_all)}')

        rules = pd.DataFrame({'rule': [str(R) for R in R_all]})
        rules['rule_len'] = [len(x) for x in rules['rule']]
        rules.to_csv(f'../data/{LANGUAGE}_rules_out.tsv', index=False, sep='\t')

    # Compute hits and scope and for each rule
    if score_rules:
        rules = pd.read_csv(f'../data/{LANGUAGE}_rules_out.tsv', sep='\t')
        #rules = rules.head(n=10)  # xxx subset for debugging
        R_all = [str2ftr_rule(R) for R in rules['rule']]

        # Score rules
        hits_all, scope_all = reliability.score_rules(R_all)
        rules['hits'] = hits_all
        rules['scope'] = scope_all
        rules.to_csv(f'../data/{LANGUAGE}_rules_scored.tsv',
                     sep='\t',
                     index=False)

    # Predict wug-test ratings (sigmorphon 2021 format)
    if evaluate_wugs:
        rules = pd.read_csv(f'../data/{LANGUAGE}_rules_scored.tsv', sep='\t')
        confidences = []
        for i in range(len(rules)):
            c = reliability.confidence(rules['hits'][i], rules['scope'][i])
            confidences.append(c)
        rules['confidence'] = confidences
        rules = rules.sort_values(by=['confidence', 'scope'], ascending=False)
        print(rules)

        wug_dev = config.wug_dev
        wug_scores = wug_test.score_mappings(wug_dev, rules)
        wug_scores = pd.DataFrame(
            wug_scores, columns=['stem', 'output', 'model_rating', 'rule_idx'])
        wug_scores = wug_scores.merge(wug_dev, how='right')
        wug_scores.to_csv(f'../data/{LANGUAGE}_wug_dev_predict.tsv',
                          sep='\t',
                          index=False)

        wug_tst = config.wug_tst
        wug_scores = wug_test.score_mappings(wug_tst, rules)
        wug_scores = pd.DataFrame(
            wug_scores, columns=['stem', 'output', 'model_rating', 'rule_idx'])
        wug_scores = wug_scores.merge(wug_tst, how='right')
        wug_scores.to_csv(f'../data/{LANGUAGE}_wug_tst_predict.tsv',
                          sep='\t',
                          index=False)


if __name__ == "__main__":
    main()