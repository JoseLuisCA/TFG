# -*- coding: utf-8 -*-
"""
Created on Mon Nov 25 09:50:48 2024

@author: EquipoAsus
"""

from production_rule import ProductionRule
from grammar import GenerativeGrammar
from TransitionStack import TransitionAutomatonStack
from automatonStack import AutomatonStack

"""Function to convert a context-free grammar to automaton stack"""

def automatonGrammar(grammar):
    variables = grammar.getVariableSymbols()
    terminal_symbols = grammar.getTerminalSymbols()
    initial_variable = grammar.getInitialSymbol()
    production_rules = grammar.getProductionRules()

    """ There is a unique state q, which is the initial state. There are no final states. """
    initial_state = "q"
    states_set = [initial_state]
    final_states_set = []
    
    """ The input alphabet is the set of terminal symbols, and the stack alphabet is the 
    variables set cup the set of terminal symbols. 
    The initial symbol of the stack is the initial variable. """
    
    input_alphabet = terminal_symbols
    stack_alphabet = variables + input_alphabet
    initial_stack_symbol = initial_variable
    
    transitions = []
    
    """ For each variable B that appears in the right part of at least one production rule,  there will be 
    a null transition. The set of transition tuples is {(q,\alpha) \mid B -> \alpha is a production}."""
    
    for variable in variables:
        transition_tuples = []
        
        for production_rule in production_rules:
            left_part = production_rule.getLeftPart()
            
            if left_part == variable:
                right_part = production_rule.getRightPart()
                
                "Convert the list of symbols of the right part into a string. "
                string_right_part = ""
                
                for symbol_right_part in right_part:
                    string_right_part +=symbol_right_part
                    
                transition_tuple = (initial_state,string_right_part)
                transition_tuples.append(transition_tuple)
                
        transition = TransitionAutomatonStack(initial_state, "", variable, transition_tuples)
        transitions.append(transition)
        
    """For each input symbol a, add a transition \delta(q,a,a) = (q, \epsilon). """
    
    null_transition_tuples = [(initial_state, "")]
    
    for input_symbol in input_alphabet:
        transition = TransitionAutomatonStack(initial_state, input_symbol, input_symbol, null_transition_tuples)
        transitions.append(transition)
        
        
    automaton_stack = AutomatonStack(states_set, input_alphabet, stack_alphabet, transitions, initial_state, final_states_set, initial_stack_symbol)
    
    return automaton_stack


""" Recursive function that computes all the right parts of the productions associated with a 
transition of the automaton stack. Its parameters are the states set of the automaton, the 
transition state, the current partial variable,  the current list of symbols of the right part, 
and the list of symbols of the remaining top. """

def computeRightPartsTransition(states_automaton, transition_state, partial_current_variable, current_right_part, remaining_top):
    next_remaining_top = remaining_top.copy()
    top_symbol = next_remaining_top.pop()
    
    """ Base case: the remaining top is composed of a unique symbol:
        add the top and the transition state to the current variable, such a variable to the current 
        right part and return the list constituted just by that part. """
    
    if len(remaining_top) == 1:
        new_right_part = current_right_part.copy() 
        current_variable = partial_current_variable + top_symbol + "," + transition_state + "]>"
        new_right_part = new_right_part + [current_variable]
        
        return [new_right_part]
        
    else:
        """ For each state q, add to the right part "D,q]>", where D is the top symbol, make the 
        partial next variable "[q,", and make a recursive call to the function.  """
        
        right_parts = []
        
        for state in states_automaton:
            current_variable = partial_current_variable + top_symbol + "," + state + "]>"
            new_right_part = current_right_part.copy()
            new_right_part = new_right_part + [current_variable]
            partial_next_variable = "<[" + state + ","
            right_parts = right_parts + computeRightPartsTransition(states_automaton, transition_state, partial_next_variable, new_right_part, next_remaining_top)

        
        return right_parts
        

""" Method to convert an automaton stack to a context-free grammar. """


def grammarAutomatonStack(automaton_stack):
    """First, we ensure that the automaton accept the languaje via the empty stack criterion. """
    automaton_empty_stack = automaton_stack.equivalentAutomatonEmptyStack()
    
    input_symbols = automaton_empty_stack.getAlphabetSymbols()
    
    """ The variables are all of the form <[q,C,p]>, where p and q are states and C 
    is a stack symbol, plus an initial variable S. """
    
    initial_variable = "S" 
    variables = [initial_variable]
    
    states_set = automaton_empty_stack.getStatesSet()
    stack_symbols = automaton_empty_stack.getStackSymbols()
    
    for state1 in states_set:
        for stack_symbol in stack_symbols:
            for state2 in states_set:
                variable = "<["+state1+"," + stack_symbol + "," + state2 + "]>"
                variables.append(variable)

    production_rules = []
    
    "For each state q, add a production rule of the form S -> [q0,Z0,q]"
    
    initial_state = automaton_empty_stack.getInitialState()
    initial_symbol_stack = automaton_stack.getInitialSymbolStack()
    
    for state in states_set:
        variable_right_part = "<[" + initial_state + "," + initial_symbol_stack + "," + state + "]>"
        right_part = [variable_right_part]
        production_rule = ProductionRule(initial_variable, right_part)
        production_rules.append(production_rule)
        
    """ Go across the transitions of the automaton. """    
    
    transitions = automaton_empty_stack.getTransitions()
    
    for transition in transitions:
        initial_state_transition = transition.getInitialState()
        input_symbol = transition.getInputSymbol()
        initial_top = transition.getInitialTop()
        
        transition_tuples = transition.getTransitionTuples()
        
        """  if (p,\epsilon) \in \delta(q,a,C) add a production rule <[q,C,p]> -> a
        For each tuple (p,D1D2,..,Dm)  \in \delta(q,a,C), with m>=1, 
        For each state qm: obtain the right parts of the production rules with
        left part <[q,C,qm]> through the previous function. """
        
        for transition_tuple in transition_tuples:
            
            if len(transition_tuple[1]) == 0: # case (p,\epsilon) \in \delta(q,a,C)
                left_part = "<[" + initial_state_transition + "," + initial_top + "," + transition_tuple[0] + "]>"
                right_part = [input_symbol]
                production_rule = ProductionRule(left_part, right_part)
                production_rules.append(production_rule)
                
            else: # case (p,D1D2,..,Dm)  \in \delta(q,a,C), with m>=1
                partial_current_variable = "<[" + transition_tuple[0] + ","
                
                for state in states_set:
                    left_part = "<[" + initial_state_transition + "," + initial_top + "," + state + "]>"
                    current_right_part = [input_symbol]
                    
                    """ Put the symbols of the new top into a list. """
                    
                    symbols_top = []
                    
                    for symbol_top in transition_tuple[1]:
                        symbols_top.append(symbol_top)
                    
                    
                    """ Obtain the right parts of all production rules via the previous function. 
                    Add a production rule for each one of such right parts. """
                    
                    right_parts = computeRightPartsTransition(states_set, state, partial_current_variable, current_right_part, symbols_top)  
                    
                    for right_part in right_parts:
                        production_rule = ProductionRule(left_part, right_part)
                        production_rules.append(production_rule)
                               
                
    
    grammar = GenerativeGrammar(variables, input_symbols, initial_variable, production_rules)
    
    return grammar