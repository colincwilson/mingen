require(tidyverse)

setwd('~/Code/Python/mingen/opennmt')
language = 'eng'

fin = str_glue('../data/{language}')
train = read_tsv(str_glue('{fin}_dat_train.tsv'))
wug_dev = read_tsv(str_glue('{fin}_wug_dev.tsv'))
wug_tst = read_tsv(str_glue('{fin}_wug_tst.tsv'))

fout = str_glue('{language}')
writeLines(train$stem, str_glue('{fout}.train.src'))
writeLines(train$output, str_glue('{fout}.train.tgt'))

writeLines(train$stem, str_glue('{fout}.valid.src'))
writeLines(train$output, str_glue('{fout}.valid.tgt'))

writeLines(wug_dev$stem, str_glue('{fout}.wug_dev.src'))
writeLines(wug_dev$output, str_glue('{fout}.wug_dev.tgt'))

writeLines(wug_tst$stem, str_glue('{fout}.wug_tst.src'))
writeLines(wug_tst$output, str_glue('{fout}.wug_tst.tgt'))

