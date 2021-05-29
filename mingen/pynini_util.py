# -*- coding: utf-8 -*-

import re
import pynini
from pynini import Arc, Fst, SymbolTable
from pynini.lib import pynutil, rewrite

# Create acceptors, unions, sigstar from symbol lists (cf. strings),
# compile rules from mingen format and apply to symbol lists.
# Note: Pynini word delimiters are "[BOS]", "[EOS]"

# todo: look at documentation for context management
# with pynini.default_token_type(token_type):
#   ...
# https://github.com/kylebgorman/Pynini/issues/8
# see also (on how operations affect SymbolTables):
# https://github.com/kylebgorman/pynini/issues/22


def sigstar(syms, markers=["⟨", "⟩"]):
    """
    Symbol table and Sigma* acceptor fom list of symbols
    (optional markers for loci of cdrewrite rule application)
    """
    symtable = SymbolTable()
    symtable.add_symbol('<eps>')  # Epsilon has id 0
    for sym in syms:
        symtable.add_symbol(sym)
    for sym in markers:
        symtable.add_symbol(sym)

    #fsts = accep(syms + markers, symtable)
    #sigstar = union(fsts).closure().optimize()
    with pynini.default_token_type(symtable):
        sigstar = pynini.string_map(syms + markers) \
                        .closure().optimize()
    return sigstar, symtable


def accep(x, symtable):
    """
    Map space-separated sequence of symbols to acceptor (identity transducer)
    [pynini built-in, see bottom of "Constructing acceptors" in documentation]
    """
    # List of sequences -> list of Fsts
    if isinstance(x, list):
        return [accep(xi, symtable) for xi in x]
    # Single sequence -> Fst
    fst = pynini.accep(x, token_type=symtable)
    return fst


def accep_(x, symtable):
    """
    Map space-separated sequence of symbols to acceptor (identity transducer)
    [demo version using primitive FST functions]
    """
    fst = Fst()
    fst.set_input_symbols(symtable)
    fst.set_output_symbols(symtable)

    x = x.split(' ')
    n = len(x)
    fst.add_states(n + 1)
    fst.set_start(0)
    fst.set_final(n)
    for i in range(n):
        iolabel = symtable.find(x[i])
        fst = fst.add_arc(i, Arc(iolabel, iolabel, 0, i + 1))
    return fst


# xxx pynini built-in?
def union(fsts):
    """ Union list of Fsts """
    fst = pynini.union(*fsts)
    # xxx check symbol table of output
    return fst


# xxx pynini built-in?
def concat(fsts):
    """ Concatenate list of Fsts """
    n = 0 if fsts is None else len(fsts)
    if n == 0:
        return None
    if n == 1:
        return fsts[0]
    fst = pynini.concat(fsts[0], fsts[1])
    for i in range(2, n):
        fst = pynini.concat(fst, fsts[i])
    # xxx check symbol table of output
    return fst


def compile_context(C, symtable):
    """
    Convert context (sequence of regexs) to Fst
    """
    # Empty context xxx document
    if C == "[ ]*":
        return C
    # Ordinary context
    fsts = []
    for regex in C.split(' '):
        # Remove grouping parens and make list of symbols
        regex = re.sub('[()]', '', regex).split('|')
        fst = union(accep(regex, symtable))
        fsts.append(fst)
    fst = concat(fsts)
    return fst


def compile_rule(A, B, C, D, sigstar, symtable):
    """
    Compile cdrewrite rule from A -> B / C __D where A and B are space-separated strings, C and D are segment regexs in (seg1|seg2|...) format
    """
    # Explicit epsilon for deletion rules, instead of pynutil.delete()
    B = re.sub('∅', '<eps>', B)
    # Insertion rule
    if A == "∅":
        change = pynutil.insert(accep(B, symtable))
    # Change or deletion rule
    else:
        fstA = accep(A, symtable)
        fstB = accep(B, symtable)
        change = pynini.cross(fstA, fstB)

    with pynini.default_token_type(symtable):
        left_context = compile_context(C, symtable)
        right_context = compile_context(D, symtable)
    fst = pynini.cdrewrite(change, left_context, right_context,
                           sigstar).optimize()
    return fst


def test():
    syms = ['aa', 'bb', 'cc', 'dd']
    sigstar_, symtable = sigstar(syms)

    # Rule aa -> bb / cc __ dd
    rule1 = compile_rule('aa', 'bb', '(cc)', '(dd)', sigstar_, symtable)
    print(rule1.print())
    rule1.draw('rule1.dot', isymbols=symtable, osymbols=symtable, portrait=True)
    # dot -Tpdf rule1.dot -o rule1.pdf

    # Apply rule to input
    input1 = accep('cc aa dd', symtable)
    output1 = (input1 @ rule1)
    print(output1.print(isymbols=symtable, osymbols=symtable))
    strpath_iter = output1.paths(input_token_type=symtable,
                                 output_token_type=symtable)
    print([x for x in strpath_iter.ostrings()])

    # Rule aa -> ∅ / cc __ dd
    rule2 = compile_rule('aa', '∅', 'cc', 'dd', sigstar_, symtable)
    output2 = (input1 @ rule2).project("output").rmepsilon()
    print(output2.print(isymbols=symtable, osymbols=symtable))
    strpath_iter = output2.paths(input_token_type=symtable,
                                 output_token_type=symtable)
    print([x for x in strpath_iter.ostrings()])


if __name__ == "__main__":
    test()