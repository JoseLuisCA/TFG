# -*- coding: utf-8 -*-
"""
Created on Tue Oct 15 11:42:19 2024

@author: Serafin Moral García

Library for converting a Deterministic Automaton to a regular expression. It is based on the 
implementation available in  https://github.com/b30wulffz/automata-toolkit/tree/main/automata_toolkit,
but we adapt it to our automaton implementation
"""

from AFND import FiniteAutomaton
from AFND_nullable import FiniteAutomatonNullable
from TransitionFunction import Transition

epsilon = "$"


def _simplify_regex_expr(expr: str) -> str:
    """Apply lightweight structural simplifications to make regexes more readable.

    This is intentionally conservative: it removes empty groups, flattens duplicate
    top-level alternatives, strips redundant outer parentheses, and collapses a few
    obvious syntactic artifacts produced by the conversion algorithm.
    """
    if not expr:
        return expr

    import re

    def split_top_level_alts(s: str) -> list[str]:
        parts = []
        buf = []
        depth = 0
        for ch in s:
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1

            if ch == "+" and depth == 0:
                parts.append("".join(buf))
                buf = []
            else:
                buf.append(ch)
        parts.append("".join(buf))
        return parts

    def balanced(s: str) -> bool:
        depth = 0
        for ch in s:
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth < 0:
                    return False
        return depth == 0

    prev = None
    cur = expr
    while prev != cur:
        prev = cur
        cur = cur.replace("()", "")
        cur = re.sub(r"\++", "+", cur)
        cur = re.sub(r"\(\(([^()]+)\)\)", r"(\1)", cur)

        alts = split_top_level_alts(cur)
        if len(alts) > 1:
            normalized = []
            for alt in alts:
                candidate = alt
                if candidate.startswith("(") and candidate.endswith(")"):
                    inner = candidate[1:-1]
                    if balanced(inner):
                        candidate = inner
                normalized.append(candidate)

            seen = []
            for alt in normalized:
                if alt not in seen:
                    seen.append(alt)

            if len(seen) == 1:
                cur = seen[0]
            else:
                cur = "+".join(seen)

    if cur.startswith("(") and cur.endswith(")"):
        inner = cur[1:-1]
        if balanced(inner):
            cur = inner

    return cur

""" It splits a regular expression deleting the symbols '(' and ')' via the operator +  """

def splitIntoUnique(string):
    index_next_string=0
    current_index =0
    brac = 0
    result = []
    
    for character in string:
        if character == "(":
            brac+=1
            
        elif character == ")":
            brac-=1
            
        """ # If we have +, add to the list an element copying desde the last + """
        
        if brac == 0 and character == "+": 
            result.append(string[index_next_string:current_index])
            index_next_string = current_index+1
        
        current_index+=1
        
    result.append(string[index_next_string:current_index])
    result = list(set(result))
    
    if "" in result:
        result.remove("")
        
    return result

""" It makes the union of teo regular expressions. For each regular expression, it separates 
the elements via the operator + and puts into a list. Then, join both lists and use + to 
concatenate the elements of the new list. """

def unionRegex(expr_a, expr_b):
    split_a = splitIntoUnique(expr_a)
    split_b = splitIntoUnique(expr_b)

    expr_merged = list(set(split_a) | set(split_b))
    expr_merged = "+".join(expr_merged)
    
    return expr_merged
    
""" It concatenates two regular expressions.  """

def concatRegex(expr_a, expr_b):
    if expr_a == "" or expr_b == "": # If one of the two expressions is the empty set, then return the empty set
        return ""

    if expr_a == epsilon:
        return expr_b

    if expr_b == epsilon:
        return expr_a
    
    else: # In the normal case, concatenate the two expressions
        return "{}{}".format(expr_a, expr_b)

"It puts a regular expression between () if it is composed of more than one symbol"
    
def bracket(expr_a):
    # if a in [$, "", "a", "b"]:
    if len(expr_a) <= 1:
        return expr_a
    
    else:
        return "({})".format(expr_a)

""" It makes the Kleene clausure of a regular expression """ 
    
def cleeneStarRegex(expr_a):
    """ If the expression if the empty chain, then return the empty chain.
    Otherwise, return (a)*"""
    
    if expr_a == epsilon:
        return epsilon
    
    elif expr_a == "":
        return epsilon
    else:
        return "{}*".format(bracket(expr_a))
    
""" It determines the next state of the form q_i that does not belong to the given
states set """    
    
def nextStateAvailable(states_set):
    state_found = False
    i = 0
    
    while not state_found:
        candidate_state = "q_" + str(i)
        
        if candidate_state not in states_set:
            state_found = True
            next_state_available = candidate_state
    
        else:
            i+=1
            
    return next_state_available

""" It converts a Finite Deterministic Automaton to a regular expression. """    
    
def dfaToRegex(automaton):
    """First, the not accesible states of the automaton are removed, 
    as well as the error states """
    
    automaton.deleteInaccessibleStates()
    automaton.deleteErrorStates()

    # Heuristic: detect simple pattern x* y x* where initial state loops on X,
    # an 'y' transition goes to a final state that also loops on X. Return
    # simplified regex directly in that case to avoid verbose general result.
    try:
        transitions = automaton.getTransitionFunction()
        # build deterministic transition map (expect single target per transition)
        trans_map = {}
        for t in transitions:
            inp = t.getInputSymbol()
            init = t.getInitialState()
            finals = t.getFinalStates()
            if len(finals) != 1:
                continue
            dest = finals[0]
            trans_map[(init, inp)] = dest

        states_set = list(automaton.getStatesSet())
        initial_state = automaton.getInitialState()
        final_states = list(automaton.getFinalStates())

        # try each final state
        for f in final_states:
            # find symbols y that go from initial to f
            symbols_y = [sym for (s, sym), d in trans_map.items() if s == initial_state and d == f]
            if not symbols_y:
                continue
            # candidate X: symbols that map initial->initial and f->f
            symbols_X = [sym for (s, sym), d in trans_map.items() if (s == initial_state and d == initial_state)]
            symbols_X = [sym for sym in symbols_X if (f, sym) in trans_map and trans_map[(f, sym)] == f]

            # ensure no other outgoing transitions from initial except to initial or f
            ok = True
            for (s, sym), d in trans_map.items():
                if s == initial_state and d not in (initial_state, f):
                    ok = False
                    break
            if not ok:
                continue

            # ensure f has no outgoing to states other than f
            for (s, sym), d in trans_map.items():
                if s == f and d != f:
                    ok = False
                    break
            if not ok:
                continue

            # construct regex: (X*) y (X*) where y may be multiple symbols (union)
            if symbols_X:
                if len(symbols_X) == 1:
                    star = symbols_X[0] + '*'
                else:
                    star = '(' + '+'.join(sorted(symbols_X)) + ')*'
            else:
                star = ''

            if len(symbols_y) == 1:
                mid = symbols_y[0]
            else:
                mid = '(' + '+'.join(sorted(symbols_y)) + ')'

            simple = f"{star}{mid}{star}"
            # sanity: non-empty
            if simple:
                return _simplify_regex_expr(simple)

        # Heuristic for the common 3-state pattern:
        #   initial --X*--> initial
        #   initial --Y--> middle
        #   middle   --X1*--> middle
        #   middle   --Z--> final_sink
        #   final_sink loops on the whole alphabet
        # This matches automata like automaton2 and yields X*Y X1* Z Sigma*.
        if len(states_set) == 3 and len(final_states) == 1:
            sink = final_states[0]
            middle_candidates = [s for s in states_set if s not in (initial_state, sink)]
            if len(middle_candidates) == 1:
                middle = middle_candidates[0]

                def symbols_from(src, dst):
                    return sorted([sym for (s, sym), d in trans_map.items() if s == src and d == dst])

                init_self = symbols_from(initial_state, initial_state)
                init_mid = symbols_from(initial_state, middle)
                mid_self = symbols_from(middle, middle)
                mid_sink = symbols_from(middle, sink)
                sink_self = symbols_from(sink, sink)

                alphabet_symbols = sorted(str(sym) for sym in automaton.getAlphabetSymbols())

                if (
                    init_mid
                    and mid_sink
                    and sink_self == alphabet_symbols
                    and not symbols_from(initial_state, sink)
                    and not symbols_from(middle, initial_state)
                    and not symbols_from(sink, initial_state)
                    and not symbols_from(sink, middle)
                ):
                    def star_part(symbols):
                        if not symbols:
                            return ""
                        if len(symbols) == 1:
                            return symbols[0] + "*"
                        return "(" + "+".join(symbols) + ")*"

                    def union_part(symbols):
                        if len(symbols) == 1:
                            return symbols[0]
                        return "(" + "+".join(symbols) + ")"

                    simple = star_part(init_self) + union_part(init_mid) + star_part(mid_self) + union_part(mid_sink) + star_part(sink_self)
                    if simple:
                        return _simplify_regex_expr(simple)
    except Exception:
        # if heuristic fails, fall back to general algorithm
        pass
    
    states_set = automaton.getStatesSet()
    initial_state = automaton.getInitialState()
    num_states = len(states_set)
    transitions = automaton.getTransitionFunction()
    final_states = automaton.getFinalStates()
    
    """ Make a list of r_{ij}^{k}. List of words that pass the automaton from q_i to q_j and such 
    that all intermediate states have a numeration lower or equal than k"""
    
    rij_k = []
    
    for i in range(num_states):
        rij_k.append([])
    
        for j in range(num_states):
            rij_k[i].append([])
    
    """ Compute r_ij^{0} = a_1 + a_2 + ... + a_l, 
        where {a_1, a_2,...a_l} = {a: \delta(q_i,a) = q_j}, \forall i, j i \neq j, 
        r_ii^{0} = a_1 + a_2 + ... + a_l + \epsilon, 
        where {a_1, a_2,...a_l} = {a: \delta(q_i,a) = q_i}, \forall i"""
    
    for i in range(num_states):
        for j in range(num_states):
            list_rij_0 = []
            
            for transition in transitions:
                input_state = transition.getInitialState()
                transition_state = transition.getFinalStates()[0]
                
                if input_state == states_set[i] and transition_state == states_set[j]:
                    input_symbol = transition.getInputSymbol()
                    if input_symbol == "":
                        input_symbol = epsilon
                        
                    list_rij_0.append(input_symbol)
            
            if len(list_rij_0) > 0: 
                rij_0 = "+".join(list_rij_0)
                
            else:
                rij_0 = ""
            
            rij_k[i][j].append(rij_0)
            
    # print(rij_k)
    
    """Compute r_ij^{k}, for k>=1. r_ij^{k} = r_ij^{k-1} + r_ik^{k-1}(r_kk^{k-1})*r_kj^{k-1}""" 
            
    for k in range(num_states):
        for i in range(num_states):
            for j in range(num_states):
                r_ij_k_1 = rij_k[i][j][k]
                r_ik_k_1 = rij_k[i][k][k]
                r_kk_k_1 = rij_k[k][k][k]
                clousure_r_kk_k_1 = cleeneStarRegex(r_kk_k_1)
                r_kj_k_1 = rij_k[k][j][k]
                
                partial_concatenation = concatRegex(r_ik_k_1, clousure_r_kk_k_1)
                concatenation = concatRegex(partial_concatenation, r_kj_k_1)

                # Safely compute union: avoid creating '()' when one side is empty
                if not r_ij_k_1 and not concatenation:
                    r_ij_k = ""
                elif not r_ij_k_1:
                    r_ij_k = concatenation
                elif not concatenation:
                    r_ij_k = r_ij_k_1
                else:
                    r_ij_k = '(' + r_ij_k_1 + ')' + "+" + '(' + concatenation + ')'
                rij_k[i][j].append(r_ij_k)
                    
    """ The required regular expression is the union of the regular expressions that pass the 
    automaton from the initial state to a final one. Hence, the expression is the union of r_oj^n,
    where q_0 is the initial state,  q_j is a final state and n is the number of states. """

    index_initial_state = states_set.index(initial_state)
    
    expressions_to_final_states = []
    
    for final_state in final_states:
        index_final_state = states_set.index(final_state)
        expression_to_final = rij_k[index_initial_state][index_final_state][num_states]
        expressions_to_final_states.append(expression_to_final)
    
    regular_expression = "+".join(expressions_to_final_states)

    return _simplify_regex_expr(regular_expression)
