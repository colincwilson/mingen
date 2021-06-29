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
    mutate(rime = gsub(str_glue('.*({vowel}.*?$)'), '\\1', rime)) ->
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

# Convert rule contexts to regexes
rules %>%
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
    # Sort by confidence
    arrange(desc(Confidence)) %>%
    identity() ->
    rules

# Regular rules xxx approx
rules %>%
    filter(A=='' & B %in% c('t', 'd', 'əd')) ->
    rules_reg

# Irregular rules xxx approx
rules %>%
    filter(!(A=='' & B %in% c('t', 'd', 'əd'))) ->
    rules_irreg

nrow(rules_reg)
nrow(rules_irreg)
quantile(rules_irreg$Confidence)

# Foci of irregular rules
#vowel_irreg = gsub(str_glue('.*({vowel}).*'), '\\1', rules_irreg$A)
#vowel_irreg = vowel_irreg[grepl(str_glue('{vowel}'), vowel_irreg)]
sort(xtabs(~ A, rules_irreg), decreasing=TRUE)
# i (42) ɪ (149) Y (102) 
# ip (13) iɹ (1) iC (1) ɪŋk (1) eɹ/ek (32) ɛl (5) ɛt (3) æn (3) æŋ (1) ʌn/ʌm 
# (4) ɔ#/ɔl (3) o#/old (10) u/ut (7)
# vowels that do not occur in foci: a|ʊ|ɚ|W|O

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

rimes %>%
    #mutate(max_confidence = replace_na(max_confidence, '0')) %>%
    mutate(irreg_apply = !is.na(max_confidence)) %>%
    arrange(desc(max_confidence), desc(n)) ->
    rimes

# Sanity check (rimes_in covers attested irregular rimes)
lex_ah03 %>%
    filter(past_type == 'irreg') ->
    lex_ah03_irreg

rimes %>%
    filter(irreg_apply) ->
    rimes_in

lex_ah03_irreg = left_join(lex_ah03_irreg, rimes_in)


# Attested rimes that can / cannot undergo any irregular rule
xtabs(~ I(max_confidence > 0.50), rimes)


# # # # # # # # # #
# A&H regular islands

# Highest-confidence rule that applies to a lemma,
# useful for finding island rules; assumes rules 
# sorted by confidence
maxRule = function(lemma, rules) {
    max_id = NA
    max_context = NA
    max_confidence = 0
    for (i in 1:nrow(rules)) {
        rule_id = rules[i,]$rule_id
        context = rules[i,]$CAD_regex
        confidence = rules[i,]$Confidence
        if (grepl(context, lemma)) {
            max_id = rule_id
            max_context = context
            max_confidence = confidence
            break
        }
    }
    return (c(
        'max_id'=max_id,
        'max_context'=max_context,
        'max_confidence'=max_confidence))
}

reg_island_wugs = c('bYz', 'blef', 'blɪg', 'bɹɛJ', 'Cul', 'dYz', 'dɹYs', 'flɪJ'
                    'fɹo', 'gɛɹ', 'gɛz', 'glɪp', 'nes', 'ɹYf', 'spæk', 'stɪn'
                    'stɪp', 'stYɹ', 'tɛʃ', 'wɪs')
maxRule('bYz', rules_reg)
maxRule('blef', rules_reg)
maxRule('blɪg', rules_reg)
maxRule('bɹɛJ', rules_reg)
maxRule('Cul', rules_reg)
maxRule('dYz', rules_reg)
maxRule('dɹYs', rules_reg)
maxRule('flɪJ', rules_reg)
maxRule('stYɹ', rules_reg)
maxRule('stɪp', rules_reg)
maxRule('stɪn', rules_reg)


# High confidence regular rules
rules %>%
     %>%
    arrange(desc(Confidence), desc(Scope)) ->
    rules_reg

rules_reg %>%
    filter(C=='X') -> rules_reg_mostgeneral
# confidence = 0.921

rules_reg %>%
    filter(Confidence > 0.921) ->
    rules_reg_highconf

rules_reg_highconf %>%
    filter(grepl('ɪ.*\\].*p', C)) %>%
    head() %>%
    view()
# n = 3678
# 23577 X [a, ɔ, ɛ, ɪ, ʊ, ʌ] p  0.980   stip
# 2451  X [e, i, o, u, ɔ, ə, ɚ, ɛ, ɪ, ʊ, ʌ] n   0.925   stin
# stire??

reg_islands = c(
    'non-high vowel + p' = '[p]$',
    'coronal + k' = '[k]$',
    'unround low + k' = '[k]$',
    'voiced velar stop' = '[g]$',
    'voiceless fricative' = '[fθsʃ]$',
    'voiced alveolar fricative' = '[vðzʒ]$',
    'post-alveolar fricative or affricate' = '[ʃʒCJ]$',
    'aɪ+ɹ ?' = 'ɹ$',
    'ʊ+l ' = 'l$')
# 

idx = 7
print(names(reg_islands)[idx])
rimes %>%
    filter(grepl(reg_islands[idx], rime)) %>%
    filter(max_confidence >= 0.50) %>%
    view()
