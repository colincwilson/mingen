# -*- coding: utf-8 -*-

import re
import pynini
from pynini import Arc, Fst, SymbolTable
from pynini.lib import pynutil, rewrite
from rules import FtrRule

# Create acceptors, unions, sigstar from symbol lists (cf. strings),
# compile rules from mingen format and apply to symbol lists.
# Note: Pynini word delimiters are "[BOS]", "[EOS]"


def accep(x, symtable):
    """
    Map space-separated sequence of symbols to acceptor (identity transducer)
    [pynini built-in, see bottom of "Constructing acceptors" in documentation]
    """
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


def union(x, symtable: SymbolTable):
    """ Union of symbols in list """
    fsts = [accep(sym, symtable) for sym in x]
    fst = pynini.union(*fsts)
    return fst


def make_sigstar(symtable: SymbolTable):
    """ Sigma* from list of symbols in SymbolTable """
    syms_ = [sym for (sym_id, sym) in symtable]
    fst = union(syms_, symtable).closure().optimize()
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
    C = union(re.sub('[()]', '', C).split('|'), symtable)
    D = union(re.sub('[()]', '', D).split('|'), symtable)

    rule = pynini.cdrewrite(change, C, D, sigstar).optimize()
    return rule

    #rule = pynini.cdrewrite(
    #    pynutil.delete(self.td), self.consonant, "[EOS]",
    #    self.sigstar).optimize()


def test():
    syms = ['<eps>', 'aa', 'bb', 'cc', 'dd']
    symtable = SymbolTable()
    for x in syms:
        symtable.add_symbol(x)

    # Sigma*
    sigstar = make_sigstar(symtable)
    print(sigstar.print())

    # Rule aa -> bb / cc __ dd
    rule1 = compile_rule('aa', 'bb', 'cc', 'dd', sigstar, symtable)
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
    rule2 = compile_rule('aa', '∅', 'cc', 'dd', sigstar, symtable)
    output2 = (input1 @ rule2).project("output").rmepsilon()
    print(output2.print(isymbols=symtable, osymbols=symtable))
    strpath_iter = output2.paths(input_token_type=symtable,
                                 output_token_type=symtable)
    print([x for x in strpath_iter.ostrings()])


if __name__ == "__main__":
    test()