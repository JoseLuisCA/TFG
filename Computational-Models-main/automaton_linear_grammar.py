# -*- coding: utf-8 -*-
"""
Created on Wed Oct 23 12:25:54 2024

@author: EquipoAsus
"""


from AFND_nullable import FiniteAutomatonNullable
from AFND import FiniteAutomaton
from grammar import GenerativeGrammar
from production_rule import ProductionRule
from TransitionFunction import Transition

"""Compute the Non-Deterministic Finite Automaton associated with the grammar. The grammar 
    must by linear by the right. """
    
def computeAssociatedAFNDLinearRight(grammar):
    linear_right = grammar.linearRight()
        
    if not linear_right:
        print("The grammar is not linear by the right")
            
    else:
        input_symbols = grammar.getTerminalSymbols()
        start_symbol = grammar.getInitialSymbol()
        variables = grammar.getVariableSymbols()
        initial_state = "[" + start_symbol + "]"
        final_state = "[]"
        states_automaton = [initial_state, final_state]
            
        """Go across the production rules. For each production A -> \alpha, add all
        subchains \beta such that \alpha = u\betha, where u is a chain of terminal symbols"""
            
        production_rules = grammar.getProductionRules()
            
        for production_rule in production_rules:
            right_part = production_rule.getRightPart()
            num_symbols_right_part = len(right_part)
            i = 0
            terminal_symbol = True
                
            while terminal_symbol and i < num_symbols_right_part:
                    
                """Add the state corresponding to the subchain of the right part that starts 
                from the current position and go until the end. """
                    
                new_state = "["
                
                for j in range(i, num_symbols_right_part):
                    new_state += right_part[j]
                    
                new_state += "]"
                    
                if new_state not in states_automaton:
                    states_automaton.append(new_state)
                    
                    # Check whether the current symbol is terminal
                if right_part[i] in input_symbols: 
                    i+=1
                           
                else:
                    terminal_symbol = False

        transitions = []
                
        """Go across the states. If the second symbol (the first one is [) is a variable A,
        and the third one is ], then go across the productions. For each production 
        A -> \alpha, add a transition \delta([A], \epsilon = \alpha). If the second symbol
        is terminal, then add a transition \delta([a\alpha],a) = [\alpha]""" 
        
        for state in states_automaton:
            if state[1] in variables:
                if state[2] == "]": # If the state is of the form [A]
                        
                    "Go across the productions, checking whether the first symbol is A"
    
                    for production in production_rules:
                        if production.getLeftPart() == state[1]:
                            transition_state = "["
                            right_part = production.getRightPart()
                            num_symbols_right_part = len(right_part)
                                
                            for i in range(num_symbols_right_part):
                                transition_state += right_part[i]
    
                            transition_state += "]"
                                    
                            transition = Transition(state, "", [transition_state])
                            transitions.append(transition)
                 
            elif state[1] in input_symbols:
                transition_state = "[" + state[2:]
                transition = Transition(state, state[1], [transition_state])
                transitions.append(transition)
                        
            
        finite_automaton = FiniteAutomatonNullable(states_automaton,input_symbols,transitions,initial_state, [final_state])
            
        return finite_automaton
    
            
"""Compute the Non-Deterministic Finite Automaton associated with a grammar. The grammar 
must by linear by the left. """
    
def computeAssociatedAFNDLinearLeft(grammar):
    linear_left = grammar.linearLeft()
        
    if not linear_left:
        print("The grammar is not linear by the left")
            
    else:
        """Compute the reverse grammar. Then, obtain the automaton associated with 
        the reverse grammar and invert such an automaton. """
            
        reverse_grammar = grammar.computeReverseGrammar()
        automaton_reverse_grammar = computeAssociatedAFNDLinearRight(reverse_grammar)
        reverse_automaton_reverse_grammar =  automaton_reverse_grammar.computeReverseAutomaton()
            
        return reverse_automaton_reverse_grammar
    
"""Find the lineal by the right Grammar associated with the automaton """
    
def grammarLinearRight(automaton):
    """The variables of the grammar are the states, the terminal symbols are the input symbols,
        and the start symbol coincides with the initial state"""
        
    variables_grammar = automaton.getStatesSet()
    terminal_symbols_grammar = automaton.getAlphabetSymbols()
    initial_variable = automaton.getInitialState()
        
    production_rules = []
    transition_function = automaton.getTransitionFunction()
        
    """For each transition \delta(p,a) = q, add a production p->aq"""
        
        
    for transition in transition_function:
        left_part = transition.getInitialState()
        transition_state = transition.getFinalStates()[0]
        right_part = [transition.getInputSymbol(), transition_state]
            
        production_rule = ProductionRule(left_part, right_part)
        production_rules.append(production_rule)
            
    final_states = automaton.getFinalStates()
                     
    "For each final state p, add p->\epsilon"
        
    for final_state in final_states:
        left_part = final_state
        right_part = [""]
             
        production_rule = ProductionRule(left_part, right_part)
        production_rules.append(production_rule)
            
    linear_right_grammar = GenerativeGrammar(variables_grammar, terminal_symbols_grammar, initial_variable, production_rules)    
            
    return linear_right_grammar

"""Find the lineal by the right Grammar associated with an automaton. Compute the reverse automaton, 
    the lineal by the right grammar corresponding to that automaton and reverse such a grammar. """
    
def grammarLinearLeft(automaton):
        automaton_linear_right = automaton.computeReverseAutomaton()
        reverse_grammar = grammarLinearRight(automaton_linear_right)
        grammar_linear_left = reverse_grammar.computeReverseGrammar()
        
        return grammar_linear_left
    
            