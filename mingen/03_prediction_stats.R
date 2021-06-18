# Submissions for SIGMORPHON 2021, part 2
require(tidyverse)
require(glmmTMB)

source('~/Languages/UniMorph/sigmorphon2021/eng_regular_past_rule.R')
source('~/Code/Python/mingen/mingen/confidence.R')

# # # # # # # # # #
# English
LANGUAGE = c('eng', 'eng2', 'eng3')[3]
SCORE_TYPE = 'confidence'

# Verify learned rules against vault
frules = str_glue('~/Code/Python/mingen/data/{LANGUAGE}_rules_scored.tsv')
frules_vault = str_glue('~/Code/Python/mingen/sigmorphon2021_vault/data/{LANGUAGE}_rules_out.tsv')
rules = read_tsv(frules)
rules_vault = read_tsv(frules_vault)
nrow(rules) == nrow(rules_vault)
rules_ = inner_join(rules, rules_vault, by = c('rule'='rule'))
nrow(rules_) == nrow(rules_vault)

# Wug-test statistics
fwug_dev = str_glue('~/Code/Python/mingen/data/{LANGUAGE}_wug_dev_predict_{SCORE_TYPE}.tsv')
#fwug_dev = str_glue('~/Code/Python/mingen/sigmorphon2021_vault/data/{LANGUAGE}_wug_dev_predict.tsv')
fwug_tst = str_glue('~/Code/Python/mingen/data/{LANGUAGE}_wug_tst_predict_{SCORE_TYPE}.tsv')
#fwug_tst_predict = 
#    str_glue('~/Code/Python/mingen/predict/mingen0_{LANGUAGE}_tst.tsv')
wug_dev = read_tsv(fwug_dev)
wug_tst = read_tsv(fwug_tst)

wug_dev %>%
    mutate(lemma = wordform1) %>%
    mutate(form = wordform2) %>%
    mutate(tag = 'V;PST;1;SG') %>%
    mutate(human_rating = human_rating/7) %>%
	mutate(model_rating = tidyr::replace_na(model_rating, replace=0)) %>%
    mutate(past_type = rep(c('reg', 'other'), nrow(wug_dev)/2)) %>%
    mutate(double_past = ifelse(past_type == 'reg' & grepl('[td] ɪ d ⋉$', output), -1, 0)) %>%
    identity() ->
    wug_dev

ggplot(wug_dev, aes(x=model_rating, y=human_rating)) + geom_point()
print(with(wug_dev, cor.test(model_rating, human_rating)))
# 0.4976706

fit_model = glmmTMB(human_rating ~ model_rating + double_past + (1 | lemma), data = wug_dev, family = beta_family())
coef_dev = fixef(fit_model)$cond
summary(fit_model)
print(AIC(fit_model)) # -111.9987

wug_tst %>%
    mutate(lemma = wordform1) %>%
    mutate(form = wordform2) %>%
    mutate(tag = 'V;PST;1;SG') %>%
    mutate(model_rating = tidyr::replace_na(model_rating, replace=0)) %>%
    mutate(past_type = rep(c('reg', 'other'), nrow(wug_tst)/2)) %>%
    mutate(double_past = ifelse(past_type == 'reg' & grepl('[td] ɪ d ⋉$', output), -1, 0)) %>%
    identity() ->
    wug_tst

wug_tst %>%
    mutate(fit_model_rating = coef_dev[2]*model_rating + coef_dev[3]*double_past) -> wug_tst

ggplot(wug_tst, aes(x=past_type, y=fit_model_rating)) + geom_point()

wug_tst %>%
    select(lemma, form, tag, model_rating = fit_model_rating) ->
    wug_tst_predict

#write_tsv(wug_tst_predict, fwug_tst_predict)

rules = read_tsv(str_glue('~/Code/Python/mingen/data/{LANGUAGE}_rules_pruned_{SCORE_TYPE}.tsv'))
rules %>%
    filter(rule_idx %in% wug_dev$rule_idx) -> 
    rules_used


# Albright-Hayes lexical data and wugs
#lex_ah03 = read_tsv('~/Researchers/HayesBruce/AlbrightHayes2003/AlbrightHayes2003_CELEXFull.tsv')
lex_ah03 = read_tsv('~/Code/Python/mingen/albrighthayes2003/AlbrightHayes2003_CELEXFull.tsv', comment='#')

#dat_ah03 = read_tsv('~/Researchers/HayesBruce/AlbrightHayes2003/AlbrightHayes2003_Wug.tsv', comment='#')
dat_ah03 = read_tsv('~/Code/Python/mingen/albrighthayes2003/AlbrightHayes2003_Wug.tsv', comment='#')

wug_ah03 = read_tsv(str_glue('~/Code/Python/mingen/data/{LANGUAGE}_wug_albrighthayes_predict_{SCORE_TYPE}.tsv'))

wug_ah03 %>%
    mutate(model_rating = tidyr::replace_na(model_rating, replace=0)) %>%
    identity() ->
    wug_ah03

rules = read_tsv(str_glue('~/Code/Python/mingen/data/{LANGUAGE}_rules_pruned.tsv'))
rules %>%
    mutate(confidence75 = mapply(confidence, hits, scope, alpha=0.75)) %>%
    mutate(confidence95 = mapply(confidence, hits, scope, alpha=0.95)) %>%
    mutate(across(c('confidence75', 'confidence95'), tidyr::replace_na, replace=0)) %>%
    identity() ->
    rules

wug_ah03 = left_join(wug_ah03, rules)
rules_used = subset(rules, rule_idx %in% wug_ah03$rule_idx)

dat_ah03 %>%
    mutate(double_past = ifelse(past_type2 == 'Regulars' & 
        grepl('[td] ə d$', past_ipa), -1, 0)) %>%
    mutate(mingen0_rule = wug_ah03$rule_idx) %>%
    mutate(mingen0_rating = wug_ah03$model_rating) %>%
    mutate(mingen_rating = `Rule-based model predicted`) %>%
    mutate(human_rating = mean_rating_phonotactic_adjusted) %>%
    identity() ->
    dat_ah03

dat_ah03 %>%
    filter(lemma_type!='Peripheral') %>%
    mutate(past_type2 = fct_relevel(past_type2, 'Regulars')) %>%
    group_by(past_type2) %>%
    group_split() %>%
    identity() ->
    dat_ah03_split

ggplot(dat_ah03, aes(x=mingen0_rating, y=mean_rating, color=past_type2)) + geom_point()
with(subset(dat_ah03, lemma_type != 'Peripheral'),
    cor.test(mingen0_rating, mean_rating)) # 0.7860636
# cf. A&H 2003, note 16: .806 (rules), .780 (analogy), .693 (1 if reg else 0)

dat_ah03 %>%
    filter(lemma_type!='Peripheral') %>%
    group_by(past_type2) %>%
    summarise(cor.test(mingen0_rating, mean_rating)$estimate) # .573, .570
# cf. A&H 2003, p.142:
# regulars      rating      0.745 (rules), 0.448 (analogy)
#               production  0.678 (rules), 0.446 (analogy)
# irregulars    rating      0.570 (rules), 0.488 (analogy)
#               production  0.333 (rules), 0.517 (analogy)

with(dat_ah03_split[[1]],
    pairs(cbind(mingen_rating, mingen0_rating, human_rating)))

# Mispredictions of mingen0 on regulars | irregulars
fit = lm(human_rating ~ mingen0_rating, dat_ah03_split[[1]])
hist(residuals(fit))
subset(dat_ah03_split[[1]], residuals(fit) < -1.0) -> tmp
view(tmp)


# # # # # # # # # #
# German, Dutch
for (LANGUAGE in c('deu', 'nld')) {
LANGUAGE='nld'
TAG = ifelse(LANGUAGE == 'deu', 'V.PTCP;PST',
      ifelse(LANGUAGE == 'nld', 'V;PST;PL',
      '???'))

# Verify learned rules against vault
frules = str_glue('~/Code/Python/mingen/data/{LANGUAGE}_rules_scored.tsv')
frules_vault = str_glue('~/Code/Python/mingen/sigmorphon2021_vault/data/{LANGUAGE}_rules_scored.tsv')
rules = read_tsv(frules)
rules_vault = read_tsv(frules_vault)
nrow(rules) == nrow(rules_vault)
rules_ = inner_join(rules, rules_vault, by=c('rule'='rule'))
nrow(rules_) == nrow(rules_vault)
all(rules_$hits.x == rules_$hits.y)
all(rules_$scope.y == rules_$scope.y)

# Wug-test statistics
#fwug_dev = str_glue('~/Code/Python/mingen/data/{LANGUAGE}_wug_dev_predict.tsv')
fwug_dev = str_glue('~/Code/Python/mingen/data/{LANGUAGE}_wug_dev_predict.tsv')
fwug_dev_vault = str_glue('~/Code/Python/mingen/sigmorphon2021_vault/data/{LANGUAGE}_wug_dev_predict.tsv')
fwug_tst = str_glue('~/Code/Python/mingen/data/{LANGUAGE}_wug_tst_predict.tsv')
fwug_tst_vault = str_glue('~/Code/Python/mingen/sigmorphon2021_vault/data/{LANGUAGE}_wug_tst_predict.tsv')
wug_dev = read_tsv(fwug_dev)
wug_dev_vault = read_tsv(fwug_dev_vault)
wug_tst = read_tsv(fwug_tst)
wug_tst_vault = read_tsv(fwug_tst_vault)

wug_dev %>%
    mutate(lemma = wordform1) %>%
    mutate(form = wordform2) %>%
    mutate(tag = TAG) %>%
    mutate(human_rating = human_rating/7) %>%
	mutate(model_rating = tidyr::replace_na(model_rating, replace=0)) %>%
    identity() ->
    wug_dev

ggplot(wug_dev, aes(x=model_rating, y=human_rating)) + geom_point()
print(with(wug_dev, cor.test(model_rating, human_rating)))
# deu: 0.7561073, nld: 0.5125955

fit_model = glmmTMB(human_rating ~ model_rating + (1 | lemma), data = wug_dev, family = beta_family())
coef_dev = fixef(fit_model)$cond
summary(fit_model)
print(AIC(fit_model))
# deu: -127.5508, nld: -58.50812

wug_tst %>%
    mutate(lemma = wordform1) %>%
    mutate(form = wordform2) %>%
    mutate(tag = TAG) %>%
    mutate(model_rating = tidyr::replace_na(model_rating, replace=0)) %>%
    identity() ->
    wug_tst

ggplot(wug_tst, aes(x=model_rating)) + geom_histogram()

wug_tst %>%
    select(lemma, form, tag, model_rating) ->
    wug_tst_predict

#write_tsv(wug_tst_predict, fwug_tst_predict)

}