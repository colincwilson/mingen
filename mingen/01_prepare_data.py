import configargparse, pickle, re, sys
from pathlib import Path
import pandas as pd

sys.path.append(str(Path('../../phtrs')))

import config
#from phtrs import phon_config, features, str_util
from phtrs import config as phon_config
from phtrs import features, str_util

# String environment.
config.epsilon = 'ϵ'
config.bos = '⋊'
config.eos = '⋉'
config.zero = '∅'
config.save_dir = Path.home() / 'Code/Python/mingen/data'
phon_config.init(config)

# Language-specific configs.
# Eng.
# Simplify or split diphthongs, zap diacritics, fix unicode.
ENG_SEG_FIXES = {
        'eɪ': 'e', 'oʊ': 'o', 'əʊ': 'o', 'aɪ': 'a ɪ', 'aʊ': 'a ʊ', \
        'ɔɪ': 'ɔ ɪ', 'ɝ': 'ɛ ɹ', 'ˠ': '', 'm̩': 'm', 'n̩': 'n', 'l̩': 'l', \
        'ɜ': 'ə', 'uːɪ': 'uː ɪ', 'ɔ̃': 'ɔ', 'ː': '', 'r': 'ɹ', 'ɡ': 'g', \
        'ʧ': 'tʃ', 'ʤ': 'dʒ'}
# Albright & Hayes 2003 training data: split diphthongs and
# rhoticized vowels, ~Britishize æ -> ɑ, fix regular past.
ALBRIGHTHAYES_SEG_FIXES = \
    {'tʃ': 't ʃ', 'dʒ': 'd ʒ', 'æ': 'ɑ', 'ɜ˞': 'ɛ ɹ', \
    'ə˞': 'ɛ ɹ', 'ɚ': 'ɛ ɹ'} | {'([td]) ə d$': '\\1 ɨ d'} # {'([td]) ə d$': '\\1 ɪ d'}

# Deu.
# Split diphthongs, fix unicode
DEU_SEG_FIXES = {
    'ai̯': 'a i', 'au̯': 'a u', 'oi̯': 'o i', 'iːə': \
    'iː ə', 'eːə': 'eː ə', 'ɛːə': 'ɛː ə', 'ɡ': 'g'}

# Nld.
NLD_SEG_FIXES = {'ɑʊ': 'ɑ ʊ', 'ɛɪ': 'ɛ ɪ', 'ʊɪ': 'ʊ ɪ', '[+]': ''}


def format_strings(dat, extra_seg_fixes=None):
    seg_fixes = config.seg_fixes
    if extra_seg_fixes is not None:
        seg_fixes = seg_fixes | extra_seg_fixes

    # Fix transcriptions (conform to phonological feature set).
    dat['stem'] = [str_util.retranscribe(x, seg_fixes) \
        for x in dat['wordform1']]
    dat['output'] = [str_util.retranscribe(x, seg_fixes) \
        for x in dat['wordform2']]
    dat['stem'] = [str_util.add_delim(x) for x in dat['stem']]
    dat['output'] = [str_util.add_delim(x) for x in dat['output']]

    # Remove prefix from output.
    if config.remove_prefix is not None:
        dat['output'] = [re.sub('⋊ ' + config.remove_prefix, '⋊', x) \
            for x in dat['output']]
    return dat


def main():
    # Select language and transcription conventions.
    parser = configargparse.ArgParser(
        config_file_parser_class=configargparse.YAMLConfigFileParser)
    parser.add('--language',
               type=str,
               choices=['eng', 'eng2', 'eng3', 'deu', 'nld', 'tiny'],
               default='tiny')
    parser.add('--wugs', action='store_true', default=False)
    args = parser.parse_args()
    LANGUAGE = args.language

    ddata = Path.home(
    ) / 'Languages/00Dictionaries/UniMorph/sigmorphon2021/2021Task0/part2'
    if LANGUAGE == 'tiny':
        ddata = Path.home() / 'Code/Python/mingen/data'

    if LANGUAGE in ['eng', 'eng2', 'eng3']:
        wordform_omit = None
        wug_morphosyn = 'V;PST;'
        config.seg_fixes = ENG_SEG_FIXES
        if LANGUAGE in ['eng2', 'eng3']:
            config.seg_fixes |= ALBRIGHTHAYES_SEG_FIXES
        config.remove_prefix = None

    if LANGUAGE == 'deu':
        wordform_omit = '[+]'
        wug_morphosyn = '^V.PTCP;PST$'
        config.seg_fixes = DEU_SEG_FIXES
        config.remove_prefix = 'g ə'

    if LANGUAGE == 'nld':
        wordform_omit = '[+]'
        wug_morphosyn = 'V;PST;PL'
        # Split diphthongs
        config.seg_fixes = NLD_SEG_FIXES
        config.remove_prefix = None

    if LANGUAGE == 'tiny':
        wordform_omit = None
        wug_morphosyn = 'V;3;SG'
        config.seg_fixes = {}
        config.remove_prefix = None

    # # # # # # # # # #
    # Training data.
    fdat = ddata / f'{LANGUAGE}.train'
    if LANGUAGE == 'eng2':
        fdat = Path('../albrighthayes2003') / 'CELEXFull_unimorph.tsv'
    if LANGUAGE == 'eng3':
        fdat = Path('../albrighthayes2003') / 'CELEXPrefixStrip_unimorph.tsv'
    dat = pd.read_csv(fdat, sep='\t', \
        names=['wordform1', 'wordform2', 'morphosyn',
            'wordform1_orth', 'wordform2_orth'])

    # Filter rows by characters in wordforms.
    if wordform_omit is not None:
        dat = dat[~(dat.wordform1.str.contains(wordform_omit))]
        dat = dat[~(dat.wordform2.str.contains(wordform_omit))]
        dat = dat.reset_index()
    print(dat)

    # Keep rows with wug-tested morphosyn (todo: could be list).
    dat = dat[(dat.morphosyn.str.contains(wug_morphosyn))]
    dat = dat.drop('morphosyn', axis=1)
    dat = dat.drop_duplicates().reset_index()

    # Format strings and save.
    dat = format_strings(dat)
    dat.to_csv( \
        config.save_dir / f'{LANGUAGE}_dat_train.tsv',
        sep='\t',
        index=False)
    config.dat_train = dat
    print('Training data')
    print(dat)
    print()

    # # # # # # # # # #
    # Wug dev set.
    WUG_DEV = LANGUAGE
    if LANGUAGE in ['eng2', 'eng3']:
        WUG_DEV = 'eng'
    fwug_dev = ddata / f'{WUG_DEV}.judgements.dev'
    wug_dev = pd.read_csv(
        fwug_dev,
        sep='\t',
        names=['wordform1', 'wordform2', 'morphosyn', 'human_rating'])
    wug_dev = wug_dev.drop('morphosyn', axis=1)

    wug_dev = format_strings(wug_dev)
    config.wug_dev = wug_dev
    wug_dev.to_csv( \
        config.save_dir / f'{LANGUAGE}_wug_dev.tsv',
        sep='\t',
        index=False)
    print('Wug dev data')
    print(wug_dev)
    print()

    # # # # # # # # # #
    # Wug test set.
    WUG_TST = LANGUAGE
    if LANGUAGE in ['eng2', 'eng3']:
        WUG_TST = 'eng'
    fwug_tst = ddata / f'{WUG_TST}.judgements.tst'

    wug_tst = pd.read_csv( \
        fwug_tst,
        sep='\t',
        names=['wordform1', 'wordform2', 'morphosyn'])
    wug_tst = wug_tst.drop('morphosyn', axis=1)

    wug_tst = format_strings(wug_tst)
    config.wug_tst = wug_tst
    wug_tst.to_csv( \
        config.save_dir / f'{LANGUAGE}_wug_tst.tsv',
        sep='\t',
        index=False)
    print('Wug test data')
    print(wug_tst)
    print()

    # # # # # # # # # #
    # Albright-Hayes wugs.
    if LANGUAGE in ['eng', 'eng2', 'eng3']:
        falbrighthayes = Path('../albrighthayes2003') / 'Wug_unimorph.tsv'
        wug_albrighthayes = pd.read_csv( \
            falbrighthayes,
            sep='\t',
            comment='#',
            names=['wordform1', 'wordform2', 'morphosyn', 'human_rating'])

        wug_albrighthayes = format_strings( \
            wug_albrighthayes,
            extra_seg_fixes=ALBRIGHTHAYES_SEG_FIXES)
        config.wug_albrighthayes = wug_albrighthayes
        wug_albrighthayes.to_csv( \
            config.save_dir / 'albrighthayes2003_wug.tsv',
            sep='\t',
            index=False)
        print('Albright-Hayes wug data')
        print(wug_albrighthayes)
        print()

    # # # # # # # # # #
    # Monosyllabic wug pool.
    if LANGUAGE in ['eng2', 'eng3'] and args.wugs:
        fwugpool = Path.home(
        ) / 'Projects/allomorphz/exp4/stim/wug_pool/wug_pool1.csv'
        wug_pool = pd.read_csv(fwugpool)
        wug_pool = wug_pool[['phon2']]
        wug_pool.columns = ['wordform1']

        # todo: diphthong-aware string splitting
        wug_pool['wordform1'] = \
            [' '.join(x) for x in wug_pool['wordform1']]

        wug_pool['wordform2'] = wug_pool['wordform1']
        wug_pool['morphosyn'] = 'V;PST;'
        wug_pool['human_rating'] = 0.0

        wug_pool = format_strings( \
            wug_pool,
            extra_seg_fixes=ALBRIGHTHAYES_SEG_FIXES)
        wug_pool.to_csv( \
            Path.home() / 'Downloads/wug_pool.tsv',
            sep='\t',
            index=False)
        print('Monosyllabic wug pool')
        print(wug_pool)
        print()

    # # # # # # # # # #
    # Phonological features
    segments = set()
    for stem in dat['stem']:
        segments |= set(stem.split())
    for output in dat['output']:
        segments |= set(output.split())
    segments -= {config.bos, config.eos}
    segments = [x for x in segments]
    segments.sort()
    print(f'Segments that appear in training data: '
          f'{segments} (n = {len(segments)})')
    print()

    #tensormorph.config.feature_dir = Path.home(
    #) / 'Code/Python/tensormorph_redup/ftrs'
    #tensormorph.config.fdata = config.save_dir / f'{LANGUAGE}.ftr'
    #fm = tensormorph.phon_features.import_features('hayes_features.csv', segments)
    # Import features from file
    feature_matrix = features.import_features(
        Path.home() / 'Code/Python/transmorph/features/hayes_features.csv',
        segments)

    # Fix up features for mingen.
    ftr_matrix = feature_matrix.ftr_matrix
    # Drop sym feature, redundant with X (Sigma*).
    ftr_matrix = ftr_matrix.drop('sym', axis=1)
    config.phon_ftrs = ftr_matrix
    config.ftr_names = list(ftr_matrix.columns.values)
    config.syms = list(ftr_matrix.index)

    # Map from symbols to feature-value dictionaries
    # and feature vectors.
    config.sym2ftrs = {}
    config.sym2ftr_vec = {}
    for i, sym in enumerate(config.syms):
        ftrs = config.phon_ftrs.iloc[i, :].to_dict()
        config.sym2ftrs[sym] = ftrs
        config.sym2ftr_vec[sym] = tuple(ftrs.values())

    # # # # # # # # # #
    # Save config.
    config_save = {}
    for key in dir(config):
        if re.search('__', key):
            continue
        config_save[key] = getattr(config, key)

    with open(config.save_dir / f'{LANGUAGE}_config.pkl', 'wb') as f:
        pickle.dump(config_save, f)


if __name__ == "__main__":
    main()
