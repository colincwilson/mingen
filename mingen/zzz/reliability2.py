# -*- coding: utf-8 -*-

import config
from rules import *
from str_util import *
import pynini
import pynini_util


def score_rules(R_all):
    """
    Hits and scope for FtrRules on training data
    todo: precompile inputs, apply to all simultaneously?
    """

    # Convert rules to explicit regexp formant
    print('Parsing rules to regexes ...')
    R_parse = []
    for idx, R in enumerate(R_all):
        R_regex = repr(R)
        AB, CD = R_regex.split(' / ')
        A, B = AB.split(' -> ')
        C, D = CD.split(' __ ')
        R_parse.append((A, B, C, D))
        #print(idx, A, B, C, D)

    # Prepare training data
    dat = config.dat_train
    stems = [str(x) for x in dat['stem']]
    outputs = [str(x) for x in dat['output']]

    # Symbol environment
    print('Adding stem ids ...')
    syms = [x for x in config.seg2ftrs]
    sigstar, symtable = pynini_util.sigstar(syms)
    #sigstar.draw('sigstar.dot')  #, layout='portrait')

    stem_ids = [f'__{i}__' for i in range(len(stems))]
    syms += stem_ids
    for stem_id in stem_ids:
        symtable.add_symbol(stem_id)
    stem_id_fsts = pynini_util.accep(stem_ids, symtable)
    stem_id_fst = pynini_util.union(stem_id_fsts)  #.minimize()
    #stem_id_fst.draw('stem_id_fst.dot')

    # Compile all stems to single input FST,
    # paths terminating in stem ids
    print('Compiling stems to monolithic input FST ...')
    inputs = [stems[i] +' '+ stem_ids[i] \
        for i in range(len(stems))]
    with pynini.default_token_type(symtable):
        input_fst = pynini.string_map([x for x in inputs])
    input_fst.set_input_symbols(symtable)
    input_fst.set_output_symbols(symtable)
    #print(f'states in input_fst: {input_fst.num_states()}')
    #input_fst.draw('input_fst.dot')

    # FST to detect rule application
    with pynini.default_token_type(symtable):
        mark_fst = sigstar + pynini_util.accep('⟨',symtable) \
                    + sigstar + stem_id_fst
    #print(f'states in mark_fst: {mark_fst.num_states()}')
    #mark_fst.draw('mark_fst.dot')

    # Apply each rules
    print('Computing rule hit/scope ...')
    hits_all = [0] * len(R_parse)
    scope_all = [0] * len(R_parse)
    for idx in range(len(R_parse)):
        hits = 0.0
        scope = 0.0
        (A, B, C, D) = R_parse[idx]
        R_fst = pynini_util.compile_rule(A, B, C, D, sigstar, symtable)
        R_fst = R_fst + stem_id_fst
        R_fst.set_input_symbols(symtable)
        R_fst.set_output_symbols(symtable)
        #R_fst.draw('R_fst.dot')

        output_fst = (input_fst @ R_fst).minimize()
        output_fst = output_fst.project('output')
        #print(f'states in output_fst: {output_fst.num_states()}')
        output_fst = (output_fst @ mark_fst).minimize()
        #print(f'states in output_fst: {output_fst.num_states()}')

        strpath_iter = output_fst.paths(input_token_type=symtable,
                                        output_token_type=symtable)
        for output in strpath_iter.ostrings():
            output, stem_id = output.split(' __')
            output = re.sub('⟨ ', '', output)
            output = re.sub(' ⟩', '', output)
            stem_id = int(re.sub('__', '', stem_id))
            if output == outputs[stem_id]:
                hits += 1.0
            scope += 1.0  # xxx assumes deterministic rules

        hits_all[idx] = hits
        scope_all[idx] = scope
        try:
            print(f'rule {idx}, hits = {hits}, scope = {scope}, '
                  f'reliability = {hits/scope}')
        except:
            print('error: rule has zero scope')
            print(f'size of data subset_ {len(subdat_)}')
            print(R_all[idx])
            print(repr(R_all[idx]))
            sys.exit(0)

    return hits_all, scope_all
