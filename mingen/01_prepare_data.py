# -*- coding: utf-8 -*-

import pickle, re, sys
from pathlib import Path
import pandas as pd

import config
from str_util import *

tensormorph_path = Path.home() / 'Code/Python/tensormorph_redup/tensormorph'
sys.path.append(str(tensormorph_path))
import tensormorph

# String environment
config.bos = '⋊'
config.eos = '⋉'
config.zero = '∅'

tensormorph.config.epsilon = 'ϵ'
tensormorph.config.bos = config.bos
tensormorph.config.eos = config.eos
tensormorph.config.wildcard = '□'

config.save_dir = Path.home() / 'Code/Python/mingen/data'


def format_strings(dat):
    # Fix transcriptions (conform to phonological feature set)
    dat['stem'] = fix_transcription(dat['wordform1'], config.seg_fixes)
    dat['output'] = fix_transcription(dat['wordform2'], config.seg_fixes)
    dat['stem'] = [add_delim(x) for x in dat['stem']]
    dat['output'] = [add_delim(x) for x in dat['output']]

    # Remove prefix from output
    if config.remove_prefix is not None:
        dat['output'] = [
            re.sub('⋊ ' + config.remove_prefix, '⋊', x) for x in dat['output']
        ]
    return dat


# Select language and transcription conventions
LANGUAGE = ['eng', 'eng2', 'eng3', 'deu', 'nld', 'tiny'][2]
ddata = Path.home() / 'Languages/UniMorph/sigmorphon2021/2021Task0/part2'
if LANGUAGE == 'tiny':
    ddata = Path.home() / 'Code/Python/mingen/data'

if LANGUAGE in ['eng', 'eng2', 'eng3']:
    wordform_omit = None
    wug_morphosyn = 'V;PST;'
    # Simplify or split diphthongs, zap diacritics, fix unicode
    config.seg_fixes = {
      'eɪ': 'e', 'oʊ': 'o', 'əʊ': 'o', 'aɪ': 'a ɪ', 'aʊ': 'a ʊ', \
      'ɔɪ': 'ɔ ɪ', 'ɝ': 'ɛ ɹ', 'ˠ': '', 'm̩': 'm', 'n̩': 'n', 'l̩': 'l', \
      'ɜ': 'ə', 'uːɪ': 'uː ɪ', 'ɔ̃': 'ɔ', 'ː': '', 'r': 'ɹ', 'ɡ': 'g'}
    # Split diphthongs and rhoticized vowels, ~British æ -> ɑ, fix regular past
    config.seg_fixes |= {'tʃ': 't ʃ', 'dʒ': 'd ʒ', 'æ': 'ɑ', 'ɜ˞': 'ɛ ɹ', \
        'ə˞': 'ɛ ɹ', 'ɚ': 'ɛ ɹ', '([td]) ə d$': '\\1 ɪ d'}
    config.remove_prefix = None

if LANGUAGE == 'deu':
    wordform_omit = '[+]'
    wug_morphosyn = '^V.PTCP;PST$'
    # Split diphthongs, fix unicode
    config.seg_fixes = {'ai̯': 'a i', 'au̯': 'a u', 'oi̯': 'o i', \
      'iːə': 'iː ə', 'eːə': 'eː ə', 'ɛːə': 'ɛː ə', 'ɡ': 'g'}
    config.remove_prefix = 'g ə'

if LANGUAGE == 'nld':
    wordform_omit = '[+]'
    wug_morphosyn = 'V;PST;PL'
    # Split diphthongs
    config.seg_fixes = {'ɑʊ': 'ɑ ʊ', 'ɛɪ': 'ɛ ɪ', 'ʊɪ': 'ʊ ɪ', '[+]': ''}
    config.remove_prefix = None

if LANGUAGE == 'tiny':
    wordform_omit = None
    wug_morphosyn = 'V;3;SG'
    config.seg_fixes = {}
    config.remove_prefix = None

# # # # # # # # # #
# Train
fdat = ddata / f'{LANGUAGE}.train'
if LANGUAGE == 'eng2':
    fdat = Path.home() \
        / 'Researchers/HayesBruce/AlbrightHayes2003/English2_ipa/CELEXFull.in.unimorph'
if LANGUAGE == 'eng3':
    fdat = Path.home() \
        / 'Researchers/HayesBruce/AlbrightHayes2003/English2_ipa/CELEXPrefixStrip.in.unimorph'
dat = pd.read_csv(fdat, sep='\t', \
    names=['wordform1', 'wordform2', 'morphosyn',
           'wordform1_orth', 'wordform2_orth'])

# Filter rows by characters in wordforms
if wordform_omit is not None:
    dat = dat[~(dat.wordform1.str.contains(wordform_omit))]
    dat = dat[~(dat.wordform2.str.contains(wordform_omit))]
    dat = dat.reset_index()
print(dat)

# Keep rows with wug-tested morphosyn xxx could be list
dat = dat[(dat.morphosyn.str.contains(wug_morphosyn))]
dat = dat.drop('morphosyn', 1)
dat = dat.drop_duplicates().reset_index()

# Format strings and save
dat = format_strings(dat)
dat.to_csv(config.save_dir / f'{LANGUAGE}_dat_train.tsv', sep='\t', index=False)
config.dat_train = dat
print('Training data')
print(dat)
print()

# # # # # # # # # #
# Wug dev
WUG_DEV = LANGUAGE
if LANGUAGE in ['eng2', 'eng3']:
    WUG_DEV = 'eng'
fwug_dev = ddata / f'{WUG_DEV}.judgements.dev'
wug_dev = pd.read_csv(
    fwug_dev,
    sep='\t',
    names=['wordform1', 'wordform2', 'morphosyn', 'human_rating'])
wug_dev = wug_dev.drop('morphosyn', 1)

wug_dev = format_strings(wug_dev)
config.wug_dev = wug_dev
wug_dev.to_csv(
    config.save_dir / f'{LANGUAGE}_wug_dev.tsv', sep='\t', index=False)
print('Wug dev data')
print(wug_dev)
print()

# # # # # # # # # #
# Wug tst
WUG_TST = LANGUAGE
if LANGUAGE in ['eng2', 'eng3']:
    WUG_TST = 'eng'
fwug_tst = ddata / f'{WUG_TST}.judgements.tst'

wug_tst = pd.read_csv(
    fwug_tst, sep='\t', names=['wordform1', 'wordform2', 'morphosyn'])
wug_tst = wug_tst.drop('morphosyn', 1)

wug_tst = format_strings(wug_tst)
config.wug_tst = wug_tst
wug_tst.to_csv(
    config.save_dir / f'{LANGUAGE}_wug_tst.tsv', sep='\t', index=False)
print('Wug test data')
print(wug_tst)
print()

# # # # # # # # # #
# Albright-Hayes wug
if LANGUAGE in ['eng', 'eng2', 'eng3']:
    falbrighthayes = Path.home() / \
        'Researchers/HayesBruce/AlbrightHayes2003/AlbrightHayes2003_Wug_sigmorphon.tsv'
    wug_albrighthayes = pd.read_csv(
        falbrighthayes,
        sep='\t',
        comment='#',
        names=['wordform1', 'wordform2', 'morphosyn', 'human_rating'])

    wug_albrighthayes = format_strings(wug_albrighthayes)
    config.wug_albrighthayes = wug_albrighthayes
    wug_albrighthayes.to_csv(
        config.save_dir / 'albrighthayes2003_wug.tsv', sep='\t', index=False)
    print('Albright-Hayes wug data')
    print(wug_albrighthayes)
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

tensormorph.config.feature_dir = Path.home(
) / 'Code/Python/tensormorph_redup/ftrs'
tensormorph.config.fdata = config.save_dir / f'{LANGUAGE}.ftr'
fm = tensormorph.phon_features.import_features('hayes_features.csv', segments)
# NB. writes feature file before fixes below

# Fix up features for mingen
phon_ftrs = pd.read_csv(config.save_dir / f'{LANGUAGE}.ftr', sep='\t', header=0)
phon_ftrs.columns.values[0] = 'seg'
segs = phon_ftrs['seg']
phon_ftrs = phon_ftrs.drop('seg', 1)  # Segment column (not a feature)
phon_ftrs = phon_ftrs.drop('sym', 1)  # Redundant with X = (Sigma*)
ftr_names = [x for x in phon_ftrs.columns.values]
config.segs = segs
config.phon_ftrs = phon_ftrs
config.ftr_names = ftr_names

# Map from segments to feature-value dictionaries and feature vectors
seg2ftrs = {}  # Feature-value dictionaries
for i, seg in enumerate(segs):
    ftrs = phon_ftrs.iloc[i, :].to_dict()
    seg2ftrs[seg] = ftrs
seg2ftrs_ = {}  # Vectorized feature matrices
for seg, ftrs in seg2ftrs.items():
    seg2ftrs_[seg] = tuple([val for key, val in ftrs.items()])
config.seg2ftrs = seg2ftrs
config.seg2ftrs_ = seg2ftrs_

# # # # # # # # # #
# Save config
config_save = {}
for key in dir(config):
    if re.search('__', key):
        continue
    config_save[key] = getattr(config, key)

with open(config.save_dir / f'{LANGUAGE}_config.pkl', 'wb') as f:
    pickle.dump(config_save, f)
