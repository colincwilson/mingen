# Submissions for SIGMORPHON 2021, part 2
require(tidyverse)
require(glmmTMB)

# # # # # # # # # #
# English
LANGUAGE = 'eng'
fwug_dev = str_glue('~/Code/Python/mingen/data/{LANGUAGE}_wug_dev_predict.tsv')
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

fit_model = glmmTMB(human_rating ~ model_rating + double_past + (1 | lemma), data = wug_dev, family = beta_family())
coef_dev = fixef(fit_model)$cond
summary(fit_model)
AIC(fit_model)

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

write_tsv(wug_tst_predict, fwug_tst_predict)


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

fit_model = glmmTMB(human_rating ~ model_rating + (1 | lemma), data = wug_dev, family = beta_family())
coef_dev = fixef(fit_model)$cond
summary(fit_model)
AIC(fit_model)

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

write_tsv(wug_tst_predict, fwug_tst_predict)

}