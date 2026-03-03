# -*- coding: utf-8 -*-
"""
Created on Wed Sep 11 10:09:13 2024

@author: EquipoAsus
"""

from TransitionFunction import Transition
from AFND import FiniteAutomaton, getPowerset

class FiniteAutomatonNullable(FiniteAutomaton):
    
    def readAutomaton(path_file):
        automaton = FiniteAutomaton.readAutomaton(path_file)
        automaton.__class__ = FiniteAutomatonNullable
        
        return automaton
    
    
    """It computes the clausure of a state, composed of those states where we can 
    move from the original state only with null transitions. It is done via a recursive
    search from the given state. """
    
    def clousureState(self, state):
        clousure = [state]
        states_to_explore = [state]
        transitions = self.getTransitionFunction()
        
        while len(states_to_explore) >= 1: # While there are more states to explore
            "Extract the first state to explore"
            state_to_explore = states_to_explore[0]
            states_to_explore.remove(state_to_explore)
            
            """Go across the transitions. For each null transition such that the input state
            is the state to explore, add each transition state in the clousure and the states 
            to explore if it is not already included in the clousure """
        
            for transition in transitions:
                input_symbol = transition.getInputSymbol()
                initial_state_transition = transition.getInitialState()
                
                if input_symbol == '' and initial_state_transition == state_to_explore:
                    final_states_transition = transition.getFinalStates()
                    
                    for transition_state in final_states_transition:
                        if transition_state not in clousure:
                            clousure.append(transition_state)
                            states_to_explore.append(transition_state)
                
                
        return clousure
    
    """ It computes the clousure of a states set. It is defined as the union of the clousure of each
    one of the states of the subset. """
    
    def clousureStatesSet(self, states_subset):
        clousure = []
        
        """For each state, compute the clousure. For each state of such a clousure, add it to the 
        global clousure if it has not been already included. """
        
        for state in states_subset:
            partial_clousure = self.clousureState(state)
            
            for state_clousure in partial_clousure:
                if state_clousure not in clousure:
                    clousure.append(state_clousure)
            
        
        return clousure
    
    
    """ It determines the \delta^{*} function given a subset of states B and a symbol a.
    Remark that this function is defined as \delta^{*}(B,a) = Cl(\cup_{q \in B}\delta(q,a)) """    
        
    def __delta_star_symbol(self, subset_states, symbol):
        """ Determine the states subset where we can moved with that symbol from the given states set. 
        Then, make the clousure of that states subset """
        
        set_states_transition = super()._delta_star_symbol(subset_states, symbol)
       
        clousure_set_states_transition = self.clousureStatesSet(set_states_transition)
        
        return clousure_set_states_transition
    
     
    """ It determines the It determines the \delta^{*} function given a subset of states B and a word u.
    Remark that this function is defined as follows: \delta^{*}(B, \epsilon) = Cl(B) 
    \delta^{*}(B, au) = \delta^{*}(\delta^{*}(B, a),u)) """
    
    def __delta_star_word(self, subset_states, word):
        
        if len(word) == 0: # Base case: if the word is \epsilon, return B
            clousure_subset_states = self.clousureStatesSet(subset_states)
            
            return clousure_subset_states
        
        else:
            first_symbol = word[0]
            remaining_word = word[1:]
            subset_first_symbol = self.__delta_star_symbol(subset_states, first_symbol) # \delta^{*}(B, a)
            set_states_transition = self.__delta_star_word(subset_first_symbol, remaining_word) # \delta^{*}(\delta^{*}(B, a),u))
    
            return set_states_transition
     
    """ It checks whether a word u is accepted by the finite automaton. It happens if, and only if
    \delta^{*}({qo}, u) contains at least one final state. """    
         
    def wordBelongs(self, word) -> bool:
        initial_state = self.getInitialState()
        set_initial_state = [initial_state]
        states_transition = self.__delta_star_word(set_initial_state, word)
        
        final_state_found = self._finalIncluded(states_transition)
        
        return final_state_found
        
        
    """ It checks whether the automaton is deterministic. It happens if, and only if,
    for each state and input symbol, there is a transition whose set of output states is singleton,
    and there are no null transitions"""   
        
    def deterministicAutomaton(self) -> bool:
        transitions = self.getTransitionFunction()
        "First, we check that there are no null transitions "
        for transition in transitions:
            if transition.getInputSymbol() == '': # If there is a null transition, return false
                return False
            
        """ Now, it is checked that, for each state and input symbol, there is a unique 
        transition state by calling the corresponding method in the superclass """
        
        deterministic_automaton = super().deterministicAutomaton()
        
        return deterministic_automaton
    
    
    """It finds the deterministic automaton corresponding to the automaton"""
        
    def transformDeterministic(self):
        deterministic = self.deterministicAutomaton()
                 
        if deterministic: # If the automaton is deterministic, there is no conversion to do 
             return self
         
        else:
             alphabet_symbols = self.getAlphabetSymbols()

             
             """Obtain the deterministic automaton without null transitions and extrat the
             states set and the final states"""
             
             deterministic_without_null = super().transformDeterministic()
             states_set = deterministic_without_null.getStatesSet()
             final_states_set = deterministic_without_null.getFinalStates()
             initial_state_without_null = deterministic_without_null.getInitialState()
             clousure_initial_state = self.clousureState(initial_state_without_null)
             initial_state_deterministic = self._correspondenceDeterministic(clousure_initial_state)
             
             power_set_states = getPowerset(self.getStatesSet())
             
            
             """Now, add the transitions of the deterministic automaton. For each subset B and 
             input symbol a, determine \delta^{*}(B,a) and compute the corresponding set. That tuple
             of three elements determine the transition
             """
            
             transitions_deterministic = []

             for subset in power_set_states:
                 corresponding_input_state = self._correspondenceDeterministic(subset)
                 
                 for symbol in alphabet_symbols:
                     states_transition = self.__delta_star_symbol(subset,symbol)
                     corresponding_state_transition = self._correspondenceDeterministic(states_transition)
                 
                     transition_deterministic = Transition(corresponding_input_state, symbol, [corresponding_state_transition])
                     transitions_deterministic.append(transition_deterministic)
                
             "Now, the deterministic automaton can be generated"
             deterministic_automaton = FiniteAutomaton(states_set, alphabet_symbols, transitions_deterministic, initial_state_deterministic, final_states_set)
        
             return deterministic_automaton
        
        
                     