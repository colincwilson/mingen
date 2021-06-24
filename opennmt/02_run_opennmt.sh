# Train generic encoder-decoder neural network with Open-NMT
# install: pip install OpenNMT-py
# example: xxx

LANG='eng' # $1
DATADIR=. # Save data
STEPS=1000 # Training steps
WORDVEC=50 # Embedding size
RNN=100 # Hidden size

# Preprocess
if true; then
    onmt_preprocess --train_src $DATADIR/${LANG}.train.src --train_tgt ${LANG}.train.tgt --valid_src ${LANG}.valid.src --valid_tgt ${LANG}.valid.tgt --save_data $DATADIR --dynamic_dict --overwrite --share_vocab
fi

# Train
if true; then
    rm $DATADIR/model_step*.pt # necessary?
    onmt_train --data $DATADIR --save_model ./model --word_vec_size $WORDVEC --encoder_type brnn --layers 1 --rnn_size $RNN --rnn_type LSTM --train_steps $STEPS --save_checkpoint_steps 100 # --copy_attn
fi

# Evaluate (train stems)
if true; then
    onmt_translate --model $DATADIR/model_step_${STEPS}.pt --src $DATADIR/${LANG}.train.src --tgt $DATADIR/${LANG}.train.tgt --output $DATADIR/${LANG}.train.pred #--verbose --n_best 5
fi

# Evaluate (wug dev)
if true; then
    onmt_translate --model $DATADIR/model_step_${STEPS}.pt --src $DATADIR/${LANG}.wug_dev.src --tgt $DATADIR/${LANG}.wug_dev.tgt --output $DATADIR/${LANG}.wug_dev.pred --verbose --log_file $DATADIR/${LANG}.wug_dev.log

    cat $DATADIR/${LANG}.wug_dev.log | \
        egrep "GOLD [0-9]+" | sed 's/.*: //' > score1
    cat $DATADIR/${LANG}.wug_dev.log | \
        egrep "GOLD SCORE" | sed 's/.*: //' > score2
    paste score1 score2 > $DATADIR/${LANG}.wug_dev.score
    rm $DATADIR/${LANG}.wug_dev.log score1 score2
fi

# Evaluate (wug tst)
if true; then
    onmt_translate --model $DATADIR/model_step_${STEPS}.pt --src $DATADIR/${LANG}.wug_tst.src --tgt $DATADIR/${LANG}.wug_tst.tgt --output $DATADIR/${LANG}.wug_tst.pred --verbose --log_file $DATADIR/${LANG}.wug_tst.log

    cat $DATADIR/${LANG}.wug_tst.log | \
        egrep "GOLD [0-9]+" | sed 's/.*: //' > score1
    cat $DATADIR/${LANG}.wug_tst.log | \
        egrep "GOLD SCORE" | sed 's/.*: //' > score2
    paste score1 score2 > $DATADIR/${LANG}.wug_tst.score
    rm $DATADIR/${LANG}.wug_tst.log score1 score2
fi