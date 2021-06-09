# Submissions for SIGMORPHON 2021, part 2
require(tidyverse)
require(glmmTMB)

source('~/Languages/UniMorph/sigmorphon2021/eng_regular_past_rule.R')

# # # # # # # # # #
# English
LANGUAGE = 'eng'
fwug_dev = str_glue('~/Code/Python/mingen/data/{LANGUAGE}_wug_dev_predict.tsv')
#fwug_dev = str_glue('~/Code/Python/mingen/sigmorphon2021_vault/data/{LANGUAGE}_wug_dev_predict.tsv')
fwug_tst = str_glue('~/Code/Python/mingen/data/{LANGUAGE}_wug_tst_predict.tsv')
fwug_tst_predict = 
    str_glue('~/Code/Python/mingen/predict/mingen0_{LANGUAGE}_tst.tsv')
wug_dev = read_tsv(fwug_dev)
wug_tst = read_tsv(fwug_tst)

wug_dev %>%
    mutate(lemma = wordform1) %>%
    mutate(form = wordform2) %>%
    mutate(tag = 'V;PST;1;SG') %>%
    mutate(human_rating = human_rating/7) %>%
	mutate(model_rating = replace_na(model_rating, 0)) %>% # No rule to predict
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

# Albright-Hayes wugs
dat_AH03 = read_tsv('~/Researchers/HayesBruce/AlbrightHayes2003/AlbrightHayes2003_Wug.tsv', comment='#')

wug_AH03 = read_tsv(str_glue('~/Code/Python/mingen/data/{LANGUAGE}_wug_albrighthayes_predict.tsv'))

wug_AH03 %>%
    mutate(model_rating = replace_na(model_rating, 0)) %>%
    identity() ->
    wug_AH03

dat_AH03$mingen_rating = dat_AH03$`Rule-based model predicted`
dat_AH03$mingen0_rating = wug_AH03$model_rating

ggplot(dat_AH03, aes(x=mingen_rating, y=mean_rating)) + geom_point()
with(subset(dat_AH03, lemma_type != 'Peripheral'),
    cor.test(model_rating, mean_rating)) # 0.7815663
# cf. A&H 2003, note 16: .806 (rules), .780 (analogy), .693 (1 if reg else 0)

dat_AH03 %>%
    filter(lemma_type != 'Peripheral') %>%
    group_by(past_type) %>%
    summarise(r = cor.test(model_rating, mean_rating)$estimate)

with(subset)


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