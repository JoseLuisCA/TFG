# -*- coding: utf-8 -*-
"""
Conversion from deterministic finite automata to regular expressions.
The implementation uses GNFA state elimination and favors correctness over brevity.
"""

from AFND import FiniteAutomaton
from AFND_nullable import FiniteAutomatonNullable
from TransitionFunction import Transition

epsilon = "$"


""" It splits a regular expression deleting the symbols '(' and ')' via the operator +  """
def splitIntoUnique(string):
    index_next_string = 0
    current_index = 0
    brac = 0
    result = []

    for character in string:
        if character == "(":
            brac += 1
        elif character == ")":
            brac -= 1

        if brac == 0 and character == "+":
            result.append(string[index_next_string:current_index])
            index_next_string = current_index + 1

        current_index += 1

    result.append(string[index_next_string:current_index])
    result = list(set(result))

    if "" in result:
        result.remove("")

    return result


""" It makes the union of two regular expressions. """
def unionRegex(expr_a, expr_b):
    if expr_a == "":
        return expr_b
    if expr_b == "":
        return expr_a
    if expr_a == expr_b:
        return expr_a

    split_a = splitIntoUnique(expr_a)
    split_b = splitIntoUnique(expr_b)
    expr_merged = list(set(split_a) | set(split_b))
    expr_merged = "+".join(sorted(expr_merged))
    return expr_merged


""" It concatenates two regular expressions. """
def concatRegex(expr_a, expr_b):
    if expr_a == "" or expr_b == "":
        return ""

    if expr_a == epsilon:
        return expr_b

    if expr_b == epsilon:
        return expr_a

    def wrap_if_needed(expr):
        if "+" in expr and not (expr.startswith("(") and expr.endswith(")")):
            return "({})".format(expr)
        return expr

    return "{}{}".format(wrap_if_needed(expr_a), wrap_if_needed(expr_b))


""" It puts a regular expression between () if it is composed of more than one symbol """
def bracket(expr_a):
    if len(expr_a) <= 1:
        return expr_a
    return "({})".format(expr_a)


""" It makes the Kleene closure of a regular expression """
def cleeneStarRegex(expr_a):
    if expr_a == epsilon:
        return epsilon
    if expr_a == "":
        return epsilon
    return "{}*".format(bracket(expr_a))


""" It determines the next state of the form q_i that does not belong to the given states set """
def nextStateAvailable(states_set):
    state_found = False
    i = 0

    while not state_found:
        candidate_state = "q_" + str(i)

        if candidate_state not in states_set:
            state_found = True
            next_state_available = candidate_state
        else:
            i += 1

    return next_state_available


""" It converts a finite deterministic automaton to a regular expression. """
def dfaToRegex(automaton):
    """Convert a finite automaton into a regular expression using GNFA elimination."""

    if automaton is None:
        return ""

    working = automaton
    working.deleteInaccessibleStates()
    working.deleteErrorStates()

    if not working.deterministicAutomaton():
        working = working.transformDeterministic()

    states = list(working.getStatesSet())
    if not states:
        return ""

    initial_state = working.getInitialState()
    final_states = list(working.getFinalStates())
    transitions = working.getTransitionFunction()

    if initial_state is None:
        return ""

    labels = {}

    def add_label(src, dst, label):
        if not label:
            return
        key = (src, dst)
        if key in labels:
            labels[key] = unionRegex(labels[key], label)
        else:
            labels[key] = label

    # Add original transitions.
    for transition in transitions:
        src = transition.getInitialState()
        symbol = transition.getInputSymbol()
        symbol = epsilon if symbol == "" else symbol
        for dst in transition.getFinalStates():
            add_label(src, dst, symbol)

    # Add GNFA start/final states.
    new_start = "__gnfa_start__"
    new_final = "__gnfa_final__"

    add_label(new_start, initial_state, epsilon)
    if initial_state in final_states:
        add_label(new_start, new_final, epsilon)
    for final_state in final_states:
        add_label(final_state, new_final, epsilon)

    elimination_order = list(states)

    for state in elimination_order:
        loop = labels.get((state, state), "")
        loop_star = cleeneStarRegex(loop)

        incoming_sources = [src for (src, dst) in list(labels.keys()) if dst == state and src != state]
        outgoing_targets = [dst for (src, dst) in list(labels.keys()) if src == state and dst != state]

        for src in incoming_sources:
            left = labels.get((src, state), "")
            for dst in outgoing_targets:
                right = labels.get((state, dst), "")
                via = concatRegex(left, concatRegex(loop_star, right))
                add_label(src, dst, via)

        for key in list(labels.keys()):
            if state in key:
                del labels[key]

    result = labels.get((new_start, new_final), "")
    
    # Clean up epsilon symbols from the result
    if result:
        result = _clean_epsilon_from_regex(result)
    
    return result


def _clean_epsilon_from_regex(regex):
    """Remove unnecessary epsilon ($) symbols from the regex expression."""
    if not regex or regex == epsilon:
        return ""
    
    # Split by + to handle union parts
    parts = regex.split("+")
    cleaned_parts = []
    
    for part in parts:
        # Remove standalone epsilon from each part
        if part != epsilon:
            cleaned_parts.append(part)
    
    # Join back, removing empty parts
    result = "+".join(cleaned_parts)
    
    # Clean up leftover +
    while "++" in result:
        result = result.replace("++", "+")
    
    result = result.strip("+")
    
    return result if result else ""
