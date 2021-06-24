# Test hypothesis that X+rime is an island of reliability for the regular rule iff no high-confidence irregular rule could apply to it
require(tidyverse)

# # # # # # # # # #
# Lexical data
#lex_ah03 = read_tsv('~/Code/Python/mingen/albrighthayes2003/CELEXFull_ipa.tsv')
read_tsv(
    '~/Library/Java/MinimalGeneralizationLearner/English2_unicode/CELEXFull_unicode.in',
    skip=9,
    col_names = c('lemma', 'past', 'freq', 'lemma_orth', 'past_orth', 'past_type', 'notes')) %>%
    select(-notes) %>%
    drop_na() ->
    lex_ah03

# Code final rime (ignoring stress) of IPA lemma
#vowel = '(i|ɪ|eɪ|ɛ|æ|a|ɔ|oʊ|ʊ|u|ʌ|ɚ|ə|aɪ|aʊ|ɔɪ)'
vowel = '(i|ɪ|e|ɛ|æ|a|ɔ|o|ʊ|u|ʌ|ɚ|ə|Y|W|O)'
lex_ah03 %>%
    mutate(rime = gsub("ˈ", "", lemma)) %>%
    mutate(rime = gsub(str_glue('.*({vowel}.*$)'), '\\1', rime)) ->
    lex_ah03

with(lex_ah03, data.frame(xtabs(~ rime + past_type))) %>%
    pivot_wider(names_from=past_type, values_from=Freq) %>%
    mutate(n = reg + irreg, irreg.prop = irreg / n) %>%
    arrange(desc(irreg.prop)) %>%
    #filter(n>10) ->
    identity() ->
    rimes

# # # # # # # # # #
# Rules from original MinGenLearner
rules = read_tsv(
    '~/Library/Java/MinimalGeneralizationLearner/English2_unicode/CELEXFull_unicode.rules')
names(rules)[1] = 'rule_id'

# Convert MinGenLearner left (C) or right (D) context to segment regex
context2regex = function(Z, type='C') {
    # Empty right-hand context
    if (Z=='' & type=='D')
        return ('$')

    # Segment regexes
    Z %>%
        gsub('\\[', '(', .) %>%
        gsub('\\]', ')', .) %>%
        gsub('(, )?~', '', .) %>%
        gsub(',', '|', .) %>%
        gsub(' ', '', .) ->
        Z_regex

    # Wildcards and word boundaries
    if (type=='C') {
        if (grepl('^X', Z_regex))
            Z_regex = gsub('^X', '', Z_regex)
        else
            Z_regex = str_glue('^{Z_regex}')
    }
    if (type=='D') {
        if (grepl('Y$', Z_regex)) 
            Z_regex = gsub('Y$', '', Z_regex)
        else
            Z_regex = str_glue('{Z_regex}$')
    }

    return(Z_regex)
}

# Irregular rules
rules %>%
    # Remove regular rules
    filter(!(is.na(A) & B %in% c('t', 'd', 'əd'))) %>%
    # Fix coding of empties
    mutate(
        A = replace_na(A, ''),
        B = replace_na(B, ''),
        C = replace_na(C, ''),
        D = replace_na(D, ''),
    ) %>%
    # Convert rule environments to regexes
    mutate(
        C_regex = sapply(C, context2regex, type='C'),
        D_regex = sapply(D, context2regex, type='D'),
        CAD_regex = str_glue('{C_regex}{A}{D_regex}')
    ) %>%
    # Code final rime of CAD
    mutate(
        CAD_rime = gsub(str_glue('.*[^|(]({vowel}.*?$)'), '\\1', CAD_regex)
    ) %>%
    # Remove low-confidence irregular rules
    filter(Confidence > .5) %>%
    arrange(desc(Confidence)) %>%
    identity() ->
    rules_irreg

nrow(rules_irreg)


# # # # # # # # # #
# Find highest-confidence irregular rule that applies to each attested rime
rimes$max_id = rep(-1, nrow(rimes))
rimes$max_context = rep('', nrow(rimes))
rimes$max_confidence = rep(0, nrow(rimes))
for (i in 1:nrow(rimes)) {
    rime = rimes[i,]$rime
    max_id = NA
    max_context = NA
    max_confidence = NA
    for (j in 1:nrow(rules_irreg)) {
        CAD_rime = rules_irreg[j,]$CAD_rime
        confidence = rules_irreg[j,]$Confidence
        if (grepl(CAD_rime, rime)) {
            max_id = rules_irreg[j,]$rule_id
            max_context = CAD_rime
            max_confidence = confidence
            print(str_glue('{max_id} {rime} {max_context} {max_confidence}'))
            break
        }
    }
    rimes[i,]$max_id = max_id
    rimes[i,]$max_context = max_context
    rimes[i,]$max_confidence = max_confidence
}

# Rimes that can / cannot undergo any irregular rule
xtabs(~ is.na(max_confidence), rimes)
rimes_in = subset(rimes, !is.na(max_confidence))
rimes_out = subset(rimes, is.na(max_confidence))
