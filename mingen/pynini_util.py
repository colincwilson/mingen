# -*- coding: utf-8 -*-

import re
import pynini
from pynini import Arc, Fst, SymbolTable
from pynini.lib import pynutil, rewrite
from rules import FtrRule

# Create acceptors, unions, sigstar from symbol lists (cf. strings),
# compile rules from mingen format and apply to symbol lists.
# Note: Pynini word delimiters are "[BOS]", "[EOS]"


def symtable(syms):
    """
    Symbol table fom list of symbols
    """
    symtable = SymbolTable()
    symtable.add_symbol('<eps>')  # Epsilon has id 0
    for sym in syms:
        symtable.add_symbol(sym)
    return symtable


def sigstar(symtable: SymbolTable):
    """ Sigma* from list of symbols in SymbolTable """
    syms = [sym for (sym_id, sym) in symtable]
    fsts = accep(syms, symtable)
    fst = union(fsts).closure().optimize()
    return fst


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
    [demo version operating using primitive FST functions]
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


def union(fsts):
    """ Union list of Fsts """
    fst = pynini.union(*fsts)
    return fst


def concat(fsts):
    """ Concate list of Fsts """
    n = 0 if fsts is None else len(fsts)
    if n == 0:
        return None
    if n == 1:
        return fsts[0]
    fst = pynini.concat(fsts[0], fsts[1])
    for i in range(2, n):
        fst = pynini.concat(fst, fsts[i])
    return fst


def compile_context(C, symtable):
    """
    Convert context (sequence of regexs) to Fst
    """
    fsts = []
    for regex in C.split(' '):
        #if regex == '(⋊)':
        #    fsts.append(pynini.accep('[BOS]'))
        #    continue
        #elif regex == '(⋉)':
        #    fsts.append(pynini.accep('[EOS]'))
        #    continue
        regex = re.sub('[()]', '', regex).split('|')
        fsts.append(union(accep(regex, symtable)))
    fst = concat(fsts)
    return fst


def compile_rule(A, B, C, D, sigstar, symtable):
    """
    Rewrite rule from A -> B / C __D where A and B are space-separated 
    strings, C and D are segment regexs in (seg1|seg2|...) format
    # xxx handle insertion rules (pynutil.insert)
    # xxx handle deletion rules (pynutil.delete)
    """
    assert ((A != "∅") or (B != "∅"))
    if A == "∅":
        change = pynutil.insert(accep(B, symtable))
    elif B == "∅":
        change = pynutil.delete(accep(A, symtable))
    else:
        fstA = accep(A, symtable)
        fstB = accep(B, symtable)
        change = pynini.cross(fstA, fstB)

    left_context = compile_context(C, symtable)
    right_context = compile_context(D, symtable)
    fst = pynini.cdrewrite(change, left_context, right_context,
                           sigstar).optimize()
    return fst


def test():
    syms = ['<eps>', 'aa', 'bb', 'cc', 'dd']
    symtable = SymbolTable()
    for x in syms:
        symtable.add_symbol(x)

    # Sigma*
    sigstar_ = sigstar(symtable)
    print(sigstar_.print())

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