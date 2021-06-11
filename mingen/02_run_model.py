# -*- coding: utf-8 -*-
# Ex. python 02_run_model.py --language eng --learn_rules --score_rules --prune_rules --rate_wugs

import configargparse, pickle, sys
from pathlib import Path
import pandas as pd

import config
from rules import *
import mingen
import reliability
import pruning
import wug_test


def main():
    parser = configargparse.ArgParser(
        config_file_parser_class=configargparse.YAMLConfigFileParser)
    parser.add(
        '--language',
        type=str,
        choices=['eng', 'eng2', 'eng3', 'deu', 'nld', 'tiny'],
        default='tiny')
    parser.add('--learn_rules', action='store_true', default=False)
    parser.add('--score_rules', action='store_true', default=False)
    parser.add('--prune_rules', action='store_true', default=False)
    parser.add('--rate_wugs', action='store_true', default=False)
    args = parser.parse_args()
    LANGUAGE = args.language

    # Import config (as created by 01_prepare_data)
    config_save = pickle.load(
        open(Path('../data') / f'{LANGUAGE}_config.pkl', 'rb'))
    for key, val in config_save.items():
        setattr(config, key, val)

    # Make word-specific (base) rules, apply recursive minimal generalization
    if args.learn_rules:
        dat_train = config.dat_train
        print('Base rules ...')
        R_base = [base_rule(w1, w2) for (w1, w2) \
            in zip(dat_train['stem'], dat_train['output'])]

        base_rules = pd.DataFrame({'rule': [str(R) for R in R_base]})
        base_rules.to_csv(
            Path('../data') / f'{LANGUAGE}_rules_base.tsv',
            index=False,
            sep='\t')

        R_ftr = [FtrRule.from_segrule(R) for R in R_base]
        R_all = mingen.generalize_rules_rec(R_ftr)
        print(f'Learned {len(R_all)} rules')

        rules = pd.DataFrame({
            'rule_idx': [idx for idx in range(len(R_all))],
            'rule': [str(R) for R in R_all]
        })
        rules['rule_regex'] = [repr(R) for R in R_all]
        #rules['rule_len'] = [len(x) for x in rules['rule']]
        rules.to_csv(
            Path('../data') / f'{LANGUAGE}_rules_out.tsv',
            index=False,
            sep='\t')

    # Compute hits and scope and for each rule
    if args.score_rules:
        rules = pd.read_csv(
            Path('../data') / f'{LANGUAGE}_rules_out.tsv', sep='\t')
        #rules = rules.head(n=10)  # xxx subset for debugging
        R_all = [FtrRule.from_str(R) for R in rules['rule']]

        # Hit and scope on train data
        hits_all, scope_all = reliability.score_rules(R_all)
        rules['hits'] = hits_all
        rules['scope'] = scope_all

        # Confidence
        rules['confidence'] = [reliability.confidence(h,s) \
            for (h,s) in zip(rules['hits'], rules['scope'])]
        rules.to_csv(
            Path('../data') / f'{LANGUAGE}_rules_scored.tsv',
            sep='\t',
            index=False)

    # Prune rules that are bounded by less minimal generalizations
    if args.prune_rules:
        rules = pd.read_csv(
            Path('../data') / f'{LANGUAGE}_rules_scored.tsv', sep='\t')
        rules_max = pruning.prune_rules(rules)
        rules_max.to_csv(
            Path('../data') / f'{LANGUAGE}_rules_pruned.tsv',
            sep='\t',
            index=False)

    # Predict wug-test ratings
    if args.rate_wugs:
        rules = pd.read_csv(
            Path('../data') / f'{LANGUAGE}_rules_pruned.tsv', sep='\t')
        print(rules)

        splits = ['dev', 'tst']  # Sigmorphon2021
        if LANGUAGE in ['eng', 'eng2', 'eng3']:
            splits.append('albrighthayes')

        for split in splits:
            wugs = getattr(config, f'wug_{split}')
            wug_ratings = wug_test.rate_wugs(wugs, rules)
            wug_ratings = pd.DataFrame(
                wug_ratings,
                columns=['stem', 'output', 'model_rating', 'rule_idx'])
            wug_ratings = wug_ratings.merge(wugs, how='right')
            wug_ratings.to_csv(
                Path('../data') / f'{LANGUAGE}_wug_{split}_predict.tsv',
                sep='\t',
                index=False)


if __name__ == "__main__":
    main()
