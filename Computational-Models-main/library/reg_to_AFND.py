# -*- coding: utf-8 -*-
"""
Created on Mon Oct 14 09:49:02 2024

@author: Serafin Moral García

Library for converting a regular expression to a Non-Finite Deterministic Automaton 
with null transitions. It is based on the implementation available in 
https://github.com/b30wulffz/automata-toolkit/tree/main/automata_toolkit, but we adapt it to 
our automaton implementation
"""

from AFND_nullable import FiniteAutomatonNullable
from TransitionFunction import Transition
from reg_to_postfix import regexToPostfix, isAlphabet

"""It computes the automaton corresponding to the empty chain. Such an automaton is composed 
of a unique state, which is initial and final. There are no transitions. """

def getAutomatonEmptyChain(input_alphabet):
    initial_state = "q_0"
    states_set = [initial_state]
    final_states_set = [initial_state]
    
    automaton_empty_chain = FiniteAutomatonNullable(states_set, input_alphabet, [], initial_state, final_states_set)
    
    return automaton_empty_chain

""" It computes the automaton corresponding to an input symbol. Such an automaton is 
composed of two states: q_1 and q_2. The initial state is q1 and the final state is q2. 
There is a unique transition from q1 to q2 with the given input symbol"""

def getAutomatonInputSymbol(symbol, input_alphabet):
    initial_state = "q_1"
    final_state = "q_2"
    states_set = [initial_state, final_state]
    final_states_set = [final_state]
    
    transition = Transition(initial_state, symbol, final_states_set)
    
    automaton_symbol = FiniteAutomatonNullable(states_set, input_alphabet, [transition], initial_state, final_states_set)
    
    return automaton_symbol   

""" For the names not to overlap, the states of both automatons must be renamed""" 

def unionStates(states_set_1, states_set_2):
    union_states = []
    
    # Rename the first set of states appending "_1" at the end
    
    for state in states_set_1:
        new_state = state + "_1"
        union_states.append(new_state)
        
    for state in states_set_2:
        new_state = state + "_2"
        union_states.append(new_state)
    
    return union_states    

""" It copies the transitions of an automaton considering that the states have been renamed.
The sufix to be added to the states is received by a parameter """

def copyTransitions(transitions, sufix):
    copied_transitions = []
    
    for transition in transitions:
        input_symbol = transition.getInputSymbol()
        initial_state = transition.getInitialState()
        final_states = transition.getFinalStates()
        
        # Create a new initial state by adding the sufix to the initial state
        
        new_initial_state = initial_state + sufix
        
        new_final_states = []
        
        for final_state in final_states:
            new_final_state = final_state + sufix
            new_final_states.append(new_final_state)
        
        copied_transition = Transition(new_initial_state, input_symbol, new_final_states)
        copied_transitions.append(copied_transition)
    
    return copied_transitions

""" It computes the automaton corresponding to the concatenation of two automatons. """

def automatonConcatenation(automaton1, automaton2,  input_alphabet):
    
    # The states set is determined by the union of states of both automatons """
    
    states_automaton1 = automaton1.getStatesSet()
    states_automaton2 = automaton2.getStatesSet()
    union_states = unionStates(states_automaton1, states_automaton2)

    # The initial state is the initial state of the first automaton appending "_1"
    initial_state_concatenation = automaton1.getInitialState() + "_1"
    
    """ The set of final states is the set of final states of the second automaton, 
    appending "_1" to each state """
    
    final_states_concatenation = []
    final_states_second_automaton = automaton2.getFinalStates()
    
    for final_state in final_states_second_automaton:
        new_final_state = final_state + "_2"
        final_states_concatenation.append(new_final_state)
        
    transitions_automaton_1 = automaton1.getTransitionFunction()
    transitions_automaton_2 = automaton2.getTransitionFunction()

    """ Copy the transitions of both automatons via the previous method. """

    copied_transitions_1 = copyTransitions(transitions_automaton_1, "_1")
    copied_transitions_2 = copyTransitions(transitions_automaton_2, "_2")
    
    transitions_concatenation = copied_transitions_1 + copied_transitions_2
    
    """For each final state of the first automaton, add a null transition to the 
    initial state of the second automaton. Again, it must be taken into account 
    that the states have been renamed. """

    initial_state_second_automaton = automaton2.getInitialState() + "_2"
    final_states_first_automaton = automaton1.getFinalStates()
    
    for final_state in final_states_first_automaton:
        corresponding_final_state = final_state + "_1"
        new_transition = Transition(corresponding_final_state,"",[initial_state_second_automaton])
        transitions_concatenation.append(new_transition)
        
    automaton_concatenation =  FiniteAutomatonNullable(union_states, input_alphabet, transitions_concatenation, initial_state_concatenation, final_states_concatenation)   
    
    return automaton_concatenation

""" It computes the automaton corresponding to the concatenation of two automatons. """

def automatonUnion(automaton1, automaton2, input_alphabet):
    
    # The states set contains the union of the states of both automatons """
    
    states_automaton1 = automaton1.getStatesSet()
    states_automaton2 = automaton2.getStatesSet()
    union_states = unionStates(states_automaton1, states_automaton2)
    
    # Add a new state q_0, the initial state os the union automaton
    
    initial_state_union = "q_0"
    union_states.append(initial_state_union)
    
    """The final states set of the union automaton is determined via the union of the final
    states sets of both automatons"""
    
    final_states_automaton_1 = automaton1.getFinalStates()
    final_states_automaton_2 = automaton2.getFinalStates()
    
    final_states_union = unionStates(final_states_automaton_1, final_states_automaton_2)
    
    transitions_automaton_1 = automaton1.getTransitionFunction()
    transitions_automaton_2 = automaton2.getTransitionFunction()

    """ Copy the transitions of both automatons. """

    copied_transitions_1 = copyTransitions(transitions_automaton_1, "_1")
    copied_transitions_2 = copyTransitions(transitions_automaton_2, "_2")
    
    transitions_union = copied_transitions_1 + copied_transitions_2
    
    "Add null transitions to the new initial state to the initial states of both automatons "
    
    initial_state_automaton1 = automaton1.getInitialState() + "_1"
    initial_state_automaton2 = automaton2.getInitialState() + "_2"

    transition_initial_state_1 = Transition(initial_state_union, "", [initial_state_automaton1])
    transition_initial_state_2 = Transition(initial_state_union, "", [initial_state_automaton2])
    
    transitions_union.append(transition_initial_state_1)
    transitions_union.append(transition_initial_state_2)
    
    automaton_union =  FiniteAutomatonNullable(union_states, input_alphabet, transitions_union, initial_state_union, final_states_union)   
    
    return automaton_union

""" It determines the first state q_i available for the automaton """

def firstStateAvailable(automaton):
    state_found = False
    states_automaton = automaton.getStatesSet()
    i = 0
    
    while not state_found:
        candidate_state = "q_" + str(i)
        
        if candidate_state not in states_automaton:
            state_found = True
            first_state_available = candidate_state
            
        else: 
            i = i+1
            
    
    return first_state_available

""" It computes the automaton corresponding to the clousure of a given automaton """

def automatonClousure(automaton, input_alphabet):
    
    """ The states set of the clousure automaton is composed of the states of the initial 
    automaton and a new initial state. That initial state is the first q_i that has not been assigned yet. """
    
    states_set_initial = automaton.getStatesSet()
    initial_state_clousure = firstStateAvailable(automaton)
    
    states_set_clousure = states_set_initial + [initial_state_clousure] 
    
    """ The set of final states is determined by the set of final states of the original
    automaton plus the new initial state """
    
    final_states_initial = automaton.getFinalStates()
    final_states_clousure = final_states_initial + [initial_state_clousure]
    
    " Init the set of transitions of the clousure automaton by the transition of the initial one. "
    
    transitions_initial = automaton.getTransitionFunction()
    transitions_clousure = []
    
    for transition in transitions_initial:
        transitions_clousure.append(transition)
    
    """ For each final state of the clousure automaton, add a null transition from 
    that state to the initial state of the original automaton. """
    
    initial_state = automaton.getInitialState()
    
    for final_state in final_states_clousure:
        transition_to_initial = Transition(final_state, "", [initial_state])
        transitions_clousure.append(transition_to_initial)
        
    automaton_clousure =  FiniteAutomatonNullable(states_set_clousure, input_alphabet, transitions_clousure, initial_state_clousure, final_states_clousure)   
    
    return automaton_clousure   


"""Rename the states of a Non Deterministic automaton for the names to be more readable """

def renameStates(automaton):
    num_states = len(automaton.getStatesSet())
    final_states_set = automaton.getFinalStates()
    transitions = automaton.getTransitionFunction()
    num_transitions = len(transitions)
    initial_state_automaton = automaton.getInitialState()
    
    for i in range(num_states):
        initial_name = automaton.getStatesSet()[i]
        
        "If the state is not of the form q_i, look for the first q_i available and rename"
        if len(initial_name) > 3: 
            new_name = firstStateAvailable(automaton)
            automaton.getStatesSet()[i] = new_name
            
            """ If it is the initial state, rename the initial state """
            
            if initial_name == initial_state_automaton:
                automaton.setInitialState(new_name)
            
            "If the state is final, rename for the set of final states"
            
            if initial_name in final_states_set:
                index_state = final_states_set.index(initial_name)
                final_states_set = automaton.getFinalStates()[index_state] = new_name
                
            "Rename the state from the transitions"
            
            for j in range(num_transitions):
                initial_state = transitions[j].getInitialState()
                states_transition = transitions[j].getFinalStates()
                
                if initial_state == initial_name: # If the state coincides with the start state 
                    transitions[j].setInitialState(new_name)
                 
                """ If the state is in the set of transition states, look for it in the 
                corresponding list and rename """
                
                if initial_name in states_transition:
                    num_states_transition = len(states_transition) 
                    
                    for k in range(num_states_transition):
                        if states_transition[k] == initial_name:
                            automaton.getTransitionFunction()[j].setFinalState(k, new_name)
                            
    return automaton

""" It converts a regular expression to a Non-Deterministic Finite Automaton with null transitions.
    First, the regular expression is converted to its postfix representation. 
    Then, it uses an automaton stack for recursively computing the automaton corresponding to 
    the regular expression. In each step, the corresponding character is used to update the stack. """
    
def regexToAutomaton(reg_expr):
    postfix_representation = regexToPostfix(reg_expr)
    empty_chain = "$"

    """ Extract the input alphabet from the postfix representation. For each character of the 
    postfix representation, check that is an alphabet character and does not coincide with 
    the empty chain. """
    
    input_alphabet = []    
    
    for character in postfix_representation:
        if isAlphabet(character) and character != empty_chain:
            if character not in input_alphabet:
                input_alphabet.append(character)
            
    automaton_stack = []  

    for character in postfix_representation:
        """ If the character is the empty chain or an alphabet character, then put 
        the corresponding automaton at the top of the stack.
        
        If the character is the concatenation (union), then extract the two last
        automatons from the stack, make the concatenation (union) automaton and put 
        it at the top of the stack. 
        
        If the character is clousure, then extract the last automaton 
        from the stack, make the clousure automaton and put it in the stack. """
        
        if character == empty_chain:
            automaton_empty = getAutomatonEmptyChain(input_alphabet)
            automaton_stack.append(automaton_empty)
            
        elif isAlphabet(character):
            automaton_character = getAutomatonInputSymbol(character, input_alphabet)
            automaton_stack.append(automaton_character)
                    
        elif character == "?": # Concatenation character 
            automaton2 = automaton_stack.pop()
            automaton1 = automaton_stack.pop()
            automaton_concatenation = automatonConcatenation(automaton1, automaton2, input_alphabet)
            automaton_stack.append(automaton_concatenation)
            
        elif character == "+": # Union character 
            automaton2 = automaton_stack.pop()
            automaton1 = automaton_stack.pop()
            automaton_union = automatonUnion(automaton1, automaton2, input_alphabet)
            automaton_stack.append(automaton_union)

        elif character == "*": # Clousure character
            automaton = automaton_stack.pop()
            automaton_clousure = automatonClousure(automaton, input_alphabet)
            automaton_stack.append(automaton_clousure)
            
    """ Once the characters of the postfix expression have been processed, the automaton
    of the regular expression is the one of the top of the stack """

    automaton_regular_expression = automaton_stack.pop()
    
    "Finally, rename the states"
    
    automaton_regular_expression = renameStates(automaton_regular_expression)

    return automaton_regular_expression            

    