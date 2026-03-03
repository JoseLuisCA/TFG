# -*- coding: utf-8 -*-
"""
Created on Tue Oct 22 10:35:32 2024

@author: Serafin
"""

""" Class for transitions in a Non-Deterministic Automaton with Stack """


alphabet_symbols_type = str # type of symbols of the input and stacks alphabets 
states_type = str # type of the states of the automaton
transition_type = (states_type, alphabet_symbols_type) # type of a transition of the automaton, state and top of symbols of the stack

class TransitionAutomatonStack:
    __initial_state: states_type # The initial state
    __input_symbol: alphabet_symbols_type # The input symbol of the transition
    __initial_top: alphabet_symbols_type # The top of the stack before the transition
    __transition_tuples:[transition_type] # The set of tuples of the transition, composed of a state and a set of symbols of the top of the stack
    
    """ The constructor of the class"""
    
    def __init__(self, initial_state, input_symbol, initial_top, transition_tuples) -> None:
        self.__initial_state = initial_state
        self.__input_symbol = input_symbol
        self.__initial_top = initial_top
        self.__transition_tuples = transition_tuples
        
    """ Method for printing the transition"""    
    def __str__(self):
        print("(" + self.__initial_state + "," + self.__input_symbol + "," + self.__initial_top + ") -> ")
        
        for transition_tuple in self.__transition_tuples:
            print(transition_tuple[0] + "," + transition_tuple[1])
      
    def getInitialState(self):
        return self.__initial_state
    
    def setInitialState(self, initial_state):
        self.__initial_state = initial_state
        
    def getInputSymbol(self):
        return self.__input_symbol
    
    def setInputSymbol(self, input_symbol):
        self.__input_symbol = input_symbol
        
    def getInitialTop(self):
        return self.__initial_top
    
    def setInitialTop(self, initial_top):
        self.__initial_top = initial_top
        
    def getTransitionTuples(self):
        return self.__transition_tuples
    
    def setTransitionTuples(self, transition_tuples):
        self.__transition_tuples = transition_tuples
        
    
        
        


    