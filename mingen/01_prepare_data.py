import pickle, re, sys
import pandas as pd

import config
from str_util import *

#os.chdir('/Users/colin/Code/Python/tensormorph_redup')
#sys.path.append('./tensormorph')
sys.path.append('/Users/colin/Code/Python/tensormorph_redup/tensormorph')
import tensormorph

# String environment
config.bos = '⋊'
config.eos = '⋉'
config.zero = '∅'
config.save_dir = '/Users/colin/Code/Python/mingen/data'

tensormorph.config.bos = config.bos
tensormorph.config.eos = config.eos
tensormorph.config.epsilon = 'ϵ'
tensormorph.config.wildcard = '□'

# Select language to prepare features, training data, wug data
LANGUAGE = ['eng', 'deu', 'nld', 'tiny'][0]
ddata = '/Users/colin/Languages/UniMorph/sigmorphon2021/2021Task0/part2'
if LANGUAGE == 'tiny':
    ddata = '/Users/colin/Code/Python/mingen/data'
fdat = f'{ddata}/{LANGUAGE}.train'
fwug_dev = f'{ddata}/{LANGUAGE}.judgements.dev'
fwug_tst = f'{ddata}/{LANGUAGE}.judgements.tst'

if LANGUAGE == 'eng':
    wordform_omit = None
    remove_prefix = None
    wug_morphosyn = 'V;PST;'
    config.seg_fixes = {
        'eɪ': 'e', 'oʊ': 'o', 'əʊ': 'o', 'aɪ': 'a ɪ', 'aʊ': 'a ʊ', \
        'ɔɪ': 'ɔ ɪ', 'ɝ': 'ɛ ɹ', 'ˠ': '', 'm̩': 'm', 'n̩': 'n', 'l̩': 'l', \
        'ɜ': 'ə', 'uːɪ': 'uː ɪ', 'ɔ̃': 'ɔ', 'ː': '', 'r': 'ɹ', 'ɡ': 'g'}
if LANGUAGE == 'deu':
    wordform_omit = '[+]'
    remove_prefix = 'g ə'
    wug_morphosyn = '^V.PTCP;PST$'
    config.seg_fixes = {'ai̯': 'a i', 'au̯': 'a u', 'oi̯': 'o i', \
        'iːə': 'iː ə', 'eːə': 'eː ə', 'ɛːə': 'ɛː ə', 'ɡ': 'g'}
if LANGUAGE == 'nld':
    wordform_omit = '[+]'
    remove_prefix = None
    wug_morphosyn = 'V;PST;PL'
    config.seg_fixes = {'ɑʊ': 'ɑ ʊ', 'ɛɪ': 'ɛ ɪ', 'ʊɪ': 'ʊ ɪ', '[+]': ''}
if LANGUAGE == 'tiny':
    wordform_omit = None
    remove_prefix = None
    wug_morphosyn = 'V;3;SG'
    config.seg_fixes = {}

# # # # # # # # # #
# Training data
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
# Fix transcriptions (conform to phonological feature set)
dat['stem'] = fix_transcription(dat['wordform1'], config.seg_fixes)
dat['output'] = fix_transcription(dat['wordform2'], config.seg_fixes)
dat['stem'] = [add_delim(x) for x in dat['stem']]
dat['output'] = [add_delim(x) for x in dat['output']]
# Remove prefix from output
if remove_prefix is not None:
    dat['output'] = [re.sub('⋊ '+ remove_prefix, '⋊', x) \
        for x in dat['output']]
dat.to_csv(f'{config.save_dir}/{LANGUAGE}_dat_train.tsv', sep='\t', index=False)
print('Training data')
print(dat)
print()

# # # # # # # # # #
# Wug dev data
wug_dev = pd.read_csv(fwug_dev, sep='\t', \
    names=['wordform1', 'wordform2', 'morphosyn', 'human_rating'])
wug_dev = wug_dev.drop('morphosyn', 1)
# Fix transcriptions
wug_dev['stem'] = fix_transcription(wug_dev['wordform1'], config.seg_fixes)
wug_dev['output'] = fix_transcription(wug_dev['wordform2'], config.seg_fixes)
wug_dev['stem'] = [add_delim(x) for x in wug_dev['stem']]
wug_dev['output'] = [add_delim(x) for x in wug_dev['output']]
# Remove prefix from output
if remove_prefix is not None:
    wug_dev['output'] = [re.sub('⋊ '+ remove_prefix, '⋊', x) \
        for x in wug_dev['output']]
wug_dev.to_csv(f'{config.save_dir}/{LANGUAGE}_wug_dev.tsv',
               sep='\t',
               index=False)
print('Wug dev data')
print(wug_dev)
print()

# # # # # # # # # #
# Wug test data
wug_tst = pd.read_csv(fwug_tst, sep='\t', \
    names=['wordform1', 'wordform2', 'morphosyn'])
wug_tst = wug_tst.drop('morphosyn', 1)
# Fix transcriptions
wug_tst['stem'] = fix_transcription(wug_tst['wordform1'], config.seg_fixes)
wug_tst['output'] = fix_transcription(wug_tst['wordform2'], config.seg_fixes)
wug_tst['stem'] = [add_delim(x) for x in wug_tst['stem']]
wug_tst['output'] = [add_delim(x) for x in wug_tst['output']]
# Remove prefix from output
if remove_prefix is not None:
    wug_tst['output'] = [re.sub('⋊ '+ remove_prefix, '⋊', x) \
        for x in wug_tst['output']]
wug_tst.to_csv(f'{config.save_dir}/{LANGUAGE}_wug_tst.tsv',
               sep='\t',
               index=False)
print('Wug test data')
print(wug_tst)
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

tensormorph.config.feature_dir = '/Users/colin/Code/Python/tensormorph_redup/ftrs'
tensormorph.config.fdata = f'{config.save_dir}/{LANGUAGE}.ftr'
fm = tensormorph.phon_features.import_features('hayes_features.csv', segments)
# NB. writes feature file before fixes below

# Fix up features
phon_ftrs = pd.read_csv(f'{config.save_dir}/{LANGUAGE}.ftr', sep='\t', header=0)
phon_ftrs.columns.values[0] = 'seg'
segs = phon_ftrs['seg']
phon_ftrs = phon_ftrs.drop('seg', 1)  # Segment column, not a feature
phon_ftrs = phon_ftrs.drop('sym', 1)  # Redundant with X = (Sigma*)
ftr_names = [x for x in phon_ftrs.columns.values]

# Map from segments to feature-value dictionaries and feature vectors
seg2ftrs = {}
for i, seg in enumerate(segs):
    ftrs = phon_ftrs.iloc[i, :].to_dict()
    seg2ftrs[seg] = ftrs
seg2ftrs_ = {}  # Vectorized feature matrices
for seg, ftrs in seg2ftrs.items():
    seg2ftrs_[seg] = tuple([val for key, val in ftrs.items()])

# # # # # # # # # #
# Save config
config.dat_train = dat
config.wug_dev = wug_dev
config.wug_tst = wug_tst
config.segs = segs
config.phon_ftrs = phon_ftrs
config.ftr_names = ftr_names
config.seg2ftrs = seg2ftrs
config.seg2ftrs_ = seg2ftrs_

config_save = {}
for key in dir(config):
    if re.search('__', key):
        continue
    config_save[key] = getattr(config, key)

with open(f'{config.save_dir}/{LANGUAGE}_config.pkl', 'wb') as f:
    pickle.dump(config_save, f)