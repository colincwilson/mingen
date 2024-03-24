# Ex. python 02_run_model.py --language eng3 --learn_rules --score_rules --prune_rules --rate_wugs
# Ex. python 02_run_mode.py --language eng3 --wug_test <wugs.csv>

# todo: scalar features, phonology, impugnment, ...

import configargparse, pickle, sys
from pathlib import Path
import pandas as pd

sys.path.append(str(Path.cwd() / '../../phtrs'))

import config
from features import *
from rules import *
import mingen
import scoring
import pruning
import wug_testing
import near_miss
from phtrs import config as phon_config


def main():
    parser = configargparse.ArgParser(
        config_file_parser_class=configargparse.YAMLConfigFileParser)
    parser.add('--language',
               type=str,
               choices=['eng', 'eng2', 'eng3', 'deu', 'nld', 'tiny'],
               default='tiny')
    parser.add( \
        '--learn_rules',
        action='store_true',
        default=False,
        help='recursive minimal generalization')
    parser.add( \
        '--cross_contexts',
        action='store_true',
        default=False,
        help='make cross-context base rules (aka dopplegangers)')
    parser.add( \
        '--score_rules',
        action='store_true',
        default=False,
        help='confidence or accuracy')
    parser.add( \
        '--prune_rules',
        action='store_true',
        default=False,
        help='maximal rules by generality, score, and length')
    parser.add( \
        '--wug_test',
        type=str,
        default=None,
        help='predict wug outputs with pruned rules')
    parser.add( \
        '--rate_wugs',
        action='store_true',
        default=False,
        help='rate inflected wugs with pruned rules')
    parser.add( \
        '--score_type',
        type=str,
        choices=['confidence', 'accuracy'],
        default='confidence')
    parser.add( \
        '--accuracy_smooth',
        type=float,
        default=10.0,
        help='denominator for smoothed accuracy')
    parser.add( \
        '--near_miss',
        action='store_true',
        default=False,
        help='generate wug items just beyond the scope of (English) irregular rules')

    args = parser.parse_args()
    LANGUAGE = args.language
    SCORE_TYPE = args.score_type
    if SCORE_TYPE == 'accuracy':
        s0 = args.accuracy_smooth
        SCORE_TYPE = f'accuracy{s0}'

    # Import config (as created by 01_prepare_data).
    #config_save = pickle.load( # bug in reading older pkl files
    #    open(Path('../data') / f'{LANGUAGE}_config.pkl', 'rb'))
    config_save = pd.read_pickle(
        open(Path('../data') / f'{LANGUAGE}_config.pkl', 'rb'))
    for key, val in config_save.items():
        setattr(config, key, val)
    phon_config.init(config_save)

    #pruning.test()
    #sys.exit(0)

    # Quick examples.
    # todo: move to utils file
    if 0:
        t_ftrs = config.sym2ftr_vec['t']
        print(ftrs2str1(t_ftrs))
        l_ftrs = config.sym2ftr_vec['l']
        tl_ftrs, _ = common_ftrs(t_ftrs, l_ftrs)
        print(tl_ftrs)
        print(ftrs2str1(tl_ftrs))
        sys.exit(0)

    # Make word-specific (base) rules then
    # apply recursive minimal generalization.
    if args.learn_rules:
        dat_train = config.dat_train
        print('Base rules ...')
        R_base = [base_rule(w1, w2) for (w1, w2) \
            in zip(dat_train['stem'], dat_train['output'])]

        if args.cross_contexts:
            R_base = cross_contexts(R_base)

        base_rules = pd.DataFrame({'rule': [str(rule) for rule in R_base]})
        base_rules.to_csv(Path('../data') / f'{LANGUAGE}_rules_base.tsv',
                          index=False,
                          sep='\t')

        R_ftr = [FtrRule.from_segrule(R) for R in R_base]
        R_all = mingen.generalize_rules_rec(R_ftr)
        print(f'Learned {len(R_all)} rules')

        rules = pd.DataFrame({
            'rule_idx': [idx for idx in range(len(R_all))],
            'rule': [str(rule) for rule in R_all]
        })
        rules['rule_regex'] = [repr(rule) for rule in R_all]
        rules['rule_len'] = [len(x) for x in rules['rule']]
        rules.to_csv(Path('../data') / f'{LANGUAGE}_rules_out.tsv',
                     index=False,
                     sep='\t')

    # Compute hits and scope and for each learned rule.
    if args.learn_rules:
        rules = pd.read_csv(Path('../data') / f'{LANGUAGE}_rules_out.tsv',
                            sep='\t')

        # Hit and scope on train data
        R_all = [FtrRule.from_str(rule) for rule in rules['rule']]
        hits_all, scope_all = scoring.score_rules(R_all)
        rules['hits'] = hits_all
        rules['scope'] = scope_all

        rules.to_csv(Path('../data') / f'{LANGUAGE}_rules_scored.tsv',
                     sep='\t',
                     index=False)

    # Score rules for confidence or accuracy.
    if args.score_rules:
        rules = pd.read_csv(Path('../data') / f'{LANGUAGE}_rules_scored.tsv',
                            sep='\t')

        # Confidence.
        # todo: adjustable alpha
        if SCORE_TYPE == 'confidence':
            rules['confidence'] = [scoring.confidence(h, s) \
                for (h,s) in zip(rules['hits'], rules['scope'])]

        # Smoothed accuracy: hits / (scope + s0).
        if re.match('^accuracy', SCORE_TYPE):
            s0 = args.accuracy_smooth
            rules[SCORE_TYPE] = [float(h)/(float(s) + s0) \
                for (h, s) in zip(rules['hits'], rules['scope'])]

        rules.to_csv(Path('../data') / f'{LANGUAGE}_rules_scored.tsv',
                     sep='\t',
                     index=False)

    # Prune rules that are bounded by more
    # general rules or have scores <= 0.
    if args.prune_rules:
        rules = pd.read_csv(Path('../data') / f'{LANGUAGE}_rules_scored.tsv',
                            sep='\t')

        rules_max = pruning.prune_rules(rules, SCORE_TYPE)
        rules_max.to_csv(Path('../data') /
                         f'{LANGUAGE}_rules_pruned_{SCORE_TYPE}.tsv',
                         sep='\t',
                         index=False)

    # Predict wug outputs with pruned rules.
    if args.wug_test:
        rules = pd.read_csv( \
            Path('../data') /
            f'{LANGUAGE}_rules_pruned_{SCORE_TYPE}.tsv',
            sep='\t')
        print('Rules:\n', rules)

        wug_file = args.wug_test
        wugs = pd.read_csv(wug_file, sep='\t')
        print('Wug-test input:\n', wugs)

        wug_results = wug_testing.wug_test(wugs,
                                           rules,
                                           SCORE_TYPE,
                                           mode='generate')
        wug_results = pd.DataFrame( \
            wug_results,
            columns=['stem', 'pred', 'model_rating', 'rule_idx'])
        wug_results = wug_results.sort_values( \
            by=['stem', 'model_rating'],
            ascending=[True, False])
        print('Wug-test output:\n', wug_results)

        wug_results.to_csv(
            Path.home() /
            f'Downloads/{Path(wug_file).stem}_{LANGUAGE}_{SCORE_TYPE}.tsv',
            sep='\t',
            index=False)

    # Assign wug-test ratings with pruned rules.
    if args.rate_wugs:
        rules = pd.read_csv(Path('../data') /
                            f'{LANGUAGE}_rules_pruned_{SCORE_TYPE}.tsv',
                            sep='\t')
        print(rules)

        splits = ['dev', 'tst']  # Sigmorphon2021
        if LANGUAGE in ['eng', 'eng2', 'eng3']:
            splits.append('albrighthayes')

        for split in splits:
            wugs = getattr(config, f'wug_{split}')
            wug_ratings = wug_testing.wug_test(wugs,
                                               rules,
                                               SCORE_TYPE,
                                               mode='rate')
            wug_ratings = pd.DataFrame(
                wug_ratings,
                columns=['stem', 'output', 'model_rating', 'rule_idx'])
            wug_ratings = wug_ratings.merge(wugs, how='right')
            wug_ratings.to_csv(
                Path('../data') /
                f'{LANGUAGE}_wug_{split}_predict_{SCORE_TYPE}.tsv',
                sep='\t',
                index=False)

    # Generate wug items just beyond the scope of irregular rules.
    if args.near_miss:
        rules = pd.read_csv(Path('../data') /
                            f'{LANGUAGE}_rules_pruned_{SCORE_TYPE}.tsv',
                            sep='\t')
        near_miss.generate_wugs(rules)


if __name__ == "__main__":
    main()
