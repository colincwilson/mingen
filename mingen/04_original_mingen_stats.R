# Predictions of original MinGenLearner

require(tidyverse)
require(glmmTMB)

source('~/Code/Python/mingen/mingen/confidence.R')

TRAIN = c('CELEXFull', 'CELEXPrefixStrip')[1]
mydir = '~/Library/Java/MinimalGeneralization/English2_unicode/sigmorphon2021/'

# # # # # # # # # #
# Sigmorphon2021 English wug data, as recoded for MinGenLearner
read_tsv(
    str_glue(mydir, 'sigmorphon2021_english_wug_dev.tsv')) %>%
    mutate(split = 'dev') -> wug_dev

read_tsv(
    str_glue(mydir, 'sigmorphon2021_english_wug_tst.tsv')) %>%
    mutate(split = 'tst') -> wug_tst

rbind(wug_dev, wug_tst) -> wug_dat
nrow(wug_dat)

# # # # # # # # # #
# Sigmorphon2021 English wug predictions from MinGenLearner
read_tsv(
    str_glue(mydir, '{TRAIN}_unicode.sum')) %>%
    select(lemma=form1, past=form2, scope, hits, reliability, confidence) %>%
    mutate(past = sub('əd$', 'ɪd', past)) %>% # Retranscribe third allomorph
    identity() ->
    wug_pred
nrow(wug_pred)

# Check confidence values
wug_pred %>%
    mutate(myconfidence = mapply(confidence, hits, scope, alpha=0.75)) %>%
    identity() -> wug_pred
with(wug_pred, plot(myconfidence, confidence))
# Errant confidence values (all related to impugnment?)
subset(wug_pred, abs(myconfidence - confidence) > 0.5)

# Compare Albright-Hayes and Sigmorphon lexicons
read_tsv(
    str_glue(mydir, 'CELEXFull_unicode.in'),
    col_names = c('lemma', 'past', 'celex_freq', 'lemma_orth', 'past_orth', 'past_type', 'notes'),
    skip=9) ->
    lex_ah03

read_tsv(
    str_glue('~/Languages/UniMorph/sigmorphon2021/2021Task0/part2/eng.train'),
    col_names = c('lemma', 'past', 'morphosyn', 'lemma_orth', 'past_orth')) %>%
    filter(grepl('V;PST;', morphosyn)) ->
    lex_sig

full_join(lex_ah03, lex_sig,
    by=c('lemma_orth'='lemma_orth')) ->
    lex

lex %>%
    filter(is.na(lemma.x)) -> lex_ah03_out # Mising from lex_ah03
lex %>%
    filter(is.na(lemma.y)) -> lex_sig_out # Missing from lex_sig

lex_sig_out %>%
    filter(past_type=='irreg') # Irregulars missing from lex_sig
# sit ~ sat, eat ~ ate, cling ~ clung, forcast ~ forcast, 
# bid ~ bid, stink ~ stunk, stink ~ stank, outrun ~ outran

# # # # # # # # # #
# Merge data and predictions on unicode keys, retaining only highest-confidence prediction for each <lemma, past> pair
left_join(wug_dat, wug_pred) %>%
    mutate(human_rating = human_rating / 7) %>%
    mutate(model_rating = confidence) %>%
    mutate(model_rating = tidyr::replace_na(model_rating, 0)) %>%
    group_by(lemma, past) %>%
    arrange(desc(model_rating), .by_group=TRUE) %>%
    slice(1) ->
    wug_dat_pred
nrow(wug_dat_pred)

# Which <lemma, past> pairs are missing from merge?


wug_dat_pred %>%
    filter(split == 'dev') -> wug_dev_pred

ggplot(wug_dev_pred, aes(x=model_rating, y=human_rating)) + geom_point()
with(wug_dev_pred, cor.test(model_rating, human_rating))
# CELEXFull 0.4863085, CELEXPrefixStrip: 0.4769243

fit_model = glmmTMB(human_rating ~ model_rating + (1 | lemma), data = wug_dev_pred, family = beta_family())
summary(fit_model)
AIC(fit_model)
# CELEXFull -100.817, CELEXPrefixStrip: -99.02455
