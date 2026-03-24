from typing import AbstractSet


# -*- coding: utf-8 -*-
"""
Class for representing a transition in a Non-Deterministic Finite Automaton
"""

alphabet_symbols_type = str # type of symbols of input alphabet
states_type = str # type of the states of the automaton

class Transition:
    __initial_state: states_type # The initial state
    __input_symbol: alphabet_symbols_type # The input of the transition
    __set_final_states: AbstractSet[states_type] # The set of states to access with the initial state and the input symbol
    
    def __init__(self, initial, symbol, final_set) -> None:
        
        self.__initial_state = initial
        self.__input_symbol = symbol
        self.__set_final_states = final_set
        
        """object.__setattr__(self, "__initial_state", initial)
        object.__setattr__(self, "__input_symbol", symbol)
        object.__setattr__(self, "__set_final_states", final_set)"""

    def __str__(self):
        print("Start state")
        print(self.__initial_state)
        print("Input symbol")
        print(self.__input_symbol)
        print("Transition states")
        print(self.__set_final_states)
        
        return ""
    
    """ Get and Set methods """
    
    def getInitialState(self):
        return self.__initial_state
    
    def getInputSymbol(self):
        return self.__input_symbol
    
    def getFinalStates(self):
        return self.__set_final_states
    
    def setInitialState(self, initial_state):
        self.__initial_state = initial_state
        
    def setInputSymbol(self, input_symbol):
        self.__input_symbol = input_symbol
    
    def setFinalStates(self, final_states):
        self.__set_final_states = final_states
        
    def setFinalState(self, i, final_state):
        self.__set_final_states[i] = final_state
        