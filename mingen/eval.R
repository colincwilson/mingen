require(tidyverse)
require(glmmTMB)

data = read_tsv('~/Code/Python/mingen/data/eng_wug_dev_predict.tsv')
#data = read_tsv('~/Code/Python/mingen/data/nld_wug_dev_predict.tsv')

data %>%
    mutate(lemma = stem) %>%
#	mutate(past_type = rep(c('reg', 'other'), nrow(wug_pred)/2)) %>%
    mutate(human_rating = human_rating/7) %>%
	mutate(model_rating = replace_na(model_rating, 0)) -> # No rule to predict
#    mutate(reg_rating = ifelse(past_type=='reg', 1, -1)) %>%
#    mutate(double_past = ifelse(grepl('[^aeiou] [td] ɪ d ⋉$', output), 1, -1))
    data

fit_model = glmmTMB(human_rating ~ model_rating + (1 | lemma), data = data, family = beta_family())
with(data, plot(model_rating, human_rating))
with(data, cor.test(model_rating, human_rating))
summary(fit_model)
AIC(fit_model)

fit_reg = glmmTMB(human_rating ~ reg_rating + double_past + (1 | lemma), data = data, family = beta_family())
with(data, plot(reg_rating, human_rating))
with(data, cor.test(reg_rating, human_rating))
summary(fit_reg)
AIC(fit_reg)