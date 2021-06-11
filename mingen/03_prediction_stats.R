# Submissions for SIGMORPHON 2021, part 2
require(tidyverse)
require(glmmTMB)

source('~/Languages/UniMorph/sigmorphon2021/eng_regular_past_rule.R')

# A&H 2003, p.127
confidence = function(hits, scope, alpha=0.55) {
    p_star = (hits + 0.5) / (scope + 1.0)
    var_est = (p_star * (1 - p_star)) / scope
    var_est = var_est**0.5
    z = qt(alpha, scope - 1.0)
    c = p_star - z * var_est
    return (c)
}

# # # # # # # # # #
# English
LANGUAGE = c('eng', 'eng2')[2]
fwug_dev = str_glue('~/Code/Python/mingen/data/{LANGUAGE}_wug_dev_predict.tsv')
#fwug_dev = str_glue('~/Code/Python/mingen/sigmorphon2021_vault/data/{LANGUAGE}_wug_dev_predict.tsv')
fwug_tst = str_glue('~/Code/Python/mingen/data/{LANGUAGE}_wug_tst_predict.tsv')
#fwug_tst_predict = 
#    str_glue('~/Code/Python/mingen/predict/mingen0_{LANGUAGE}_tst.tsv')
wug_dev = read_tsv(fwug_dev)
wug_tst = read_tsv(fwug_tst)

wug_dev %>%
    mutate(lemma = wordform1) %>%
    mutate(form = wordform2) %>%
    mutate(tag = 'V;PST;1;SG') %>%
    mutate(human_rating = human_rating/7) %>%
	mutate(model_rating = replace_na(model_rating, value=0)) %>% # No rule
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
    mutate(model_rating = replace_na(model_rating, 0)) %>%
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

# Albright-Hayes lexical data and wugs
#lex_ah03 = read_tsv('~/Researchers/HayesBruce/AlbrightHayes2003/AlbrightHayes2003_CELEXFull.tsv')
lex_ah03 = read_tsv('~/Downloads/AlbrightHayes2003_CELEXFull.tsv')

#dat_ah03 = read_tsv('~/Researchers/HayesBruce/AlbrightHayes2003/AlbrightHayes2003_Wug.tsv', comment='#')
dat_ah03 = read_tsv('~/Downloads/AlbrightHayes2003_Wug.tsv', comment='#')

wug_ah03 = read_tsv(str_glue('~/Code/Python/mingen/data/{LANGUAGE}_wug_albrighthayes_predict.tsv'))

wug_ah03 %>%
    mutate(model_rating = replace_na(model_rating, value=0)) %>%
    identity() ->
    wug_ah03

rules = read_tsv(str_glue('~/Code/Python/mingen/data/{LANGUAGE}_rules_scored.tsv'))
rules %>%
    mutate(confidence75 = mapply(confidence, hits, scope, alpha=0.75)) %>%
    mutate(confidence95 = mapply(confidence, hits, scope, alpha=0.95)) %>%
    mutate(across(c('confidence75', 'confidence95'), replace_na, value=0)) %>%
    identity() ->
    rules

wug_ah03 = left_join(wug_ah03, rules)

dat_ah03$mingen0_rule = wug_ah03$rule_idx
dat_ah03$mingen0_rating = wug_ah03$model_rating
dat_ah03$mingen_rating = dat_ah03$`Rule-based model predicted`
dat_ah03$human_rating = dat_ah03$mean_rating
dat_ah03 %>%
    filter(lemma_type!='Peripheral') %>%
    mutate(past_type2 = fct_relevel(past_type2, 'Regulars')) %>%
    group_by(past_type2) %>%
    group_split() %>%
    identity() ->
    dat_ah03_split


ggplot(dat_ah03, aes(x=mingen0_rating, y=mean_rating, color=past_type2)) + geom_point()
with(subset(dat_ah03, lemma_type != 'Peripheral'),
    cor.test(mingen0_rating, mean_rating)) # 0.7815663
# cf. A&H 2003, note 16: .806 (rules), .780 (analogy), .693 (1 if reg else 0)

dat_ah03 %>%
    filter(lemma_type!='Peripheral') %>%
    group_by(past_type2) %>%
    summarise(cor.test(mingen_rating, mean_rating)$estimate)

with(dat_ah03_split[[1]],
    pairs(cbind(mingen_rating, mingen0_rating, human_rating)))


# # # # # # # # # #
# German, Dutch
for (LANGUAGE in c('deu', 'nld')) {

fwug_dev = str_glue('~/Code/Python/mingen/data/{LANGUAGE}_wug_dev_predict.tsv')
fwug_tst = str_glue('~/Code/Python/mingen/data/{LANGUAGE}_wug_tst_predict.tsv')
fwug_tst_predict = 
    str_glue('~/Code/Python/mingen/predict/mingen0_{LANGUAGE}_tst.tsv')
wug_dev = read_tsv(fwug_dev)
wug_tst = read_tsv(fwug_tst)

wug_dev %>%
    mutate(lemma = wordform1) %>%
    mutate(form = wordform2) %>%
    mutate(tag = 'V.PTCP;PST') %>%
    mutate(human_rating = human_rating/7) %>%
	mutate(model_rating = replace_na(model_rating, 0)) %>% # No rule to predict
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
    mutate(tag = 'V.PTCP;PST') %>%
    mutate(model_rating = replace_na(model_rating, 0)) %>%
    identity() ->
    wug_tst

ggplot(wug_tst, aes(x=model_rating)) + geom_histogram()

wug_tst %>%
    select(lemma, form, tag, model_rating) ->
    wug_tst_predict

#write_tsv(wug_tst_predict, fwug_tst_predict)

}