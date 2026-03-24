# -*- coding: utf-8 -*-
"""
Created on Tue Oct 22 10:32:59 2024

@author: Serafin
"""

from typing import AbstractSet
from TransitionStack import TransitionAutomatonStack
from Utils import extractSubsetFromLine, createStringList


""" Class for Non-Deterministic Automaton with Stack """

alphabet_symbols_type = str # type of symbols of the input and stack alphabets
states_type = str # type of the states of the automaton

class AutomatonStack:
    __states_set: AbstractSet[states_type] # The set of states of the automaton
    __alphabet_symbols: AbstractSet[alphabet_symbols_type] # The input alphabet
    __stack_symbols: AbstractSet[alphabet_symbols_type] # The stack alphabet
    __transition_function: AbstractSet[TransitionAutomatonStack] # The transition function
    __initial_state: states_type # The initial state 
    __final_states: AbstractSet[states_type] # The set of final states 
    __initial_symbol_stack: alphabet_symbols_type # The initial symbol of the stack

    """ The constructor of the class. It initializes the attributes and validates
    the initial and final states, the initial symbol of the stack, and the transitions. """
    
    def __init__(self, states_set, alphabet_symbols, stack_symbols, transitions, initial_state, final_states, initial_symbol_stack):
        self.__states_set = states_set
        self.__alphabet_symbols = alphabet_symbols
        self.__stack_symbols = stack_symbols
        self.__transition_function = transitions
        self.__initial_state = initial_state
        self.__final_states = final_states
        self.__initial_symbol_stack = initial_symbol_stack
        
    """ Get and Set methods """
    
    def getStatesSet(self):
        return self.__states_set
    
    def setStatesSet(self, states_set):
        self.__states_set = states_set
        
    def getAlphabetSymbols(self):
        return self.__alphabet_symbols
    
    def setAlphabetSymbols(self, alphabet_symbols):
        self.__alphabet_symbols = alphabet_symbols
        
    def getStackSymbols(self):
        return self.__stack_symbols
    
    def setStackSymbols(self, stack_symbols):
        self.__stack_symbols = stack_symbols
        
    def getTransitions(self):
        return self.__transition_function
    
    def setTransitions(self, transitions):
        self.__transition_function = transitions
        
    
    def getInitialState(self):
        return self.__initial_state
    
    def setInitialState(self, initial_state):
        self.__initial_state = initial_state
        
    def getInitialSymbolStack(self):
        return self.__initial_symbol_stack
    
    def setInitialSymbolStack(self, initial_symbol_stack):
        self.__initial_symbol_stack = initial_symbol_stack
        
    def getFinalStates(self):
        return self.__final_states
    
    def setFinalStates(self, final_states):
        self.__final_states = final_states 
       
    """ Static method that creates an automaton with stack
    from a list of strings. """    
        
    @staticmethod
    def __fromText(lines): 
        transitions = []
        
        """ Obtain the list of states, input symbols, stack symbols, initial 
        state, initial symbol of the stack, final states and transitions. 
        The list to obtain depends on the first character of the line. """
        
        for line in lines:
            first_character = line[0]
            
            if first_character == 'Q': # extract the states, assuming that the initial state is the first one
               states = extractSubsetFromLine(line, ",", "{")
               
            elif first_character == 'A': # extract the input symbols
                input_symbols = extractSubsetFromLine(line, ",", "{")
                
            elif first_character == 'B': # extract the stack symbols, assuming that the first symbol of the stack is the first one
                stack_symbols = extractSubsetFromLine(line, ",", "{")
                
            elif first_character == 'q': # Extract the initial state 
                initial_state = extractSubsetFromLine(line, ",", "{")[0]
                
            elif first_character == 'Z': # Extract the initial symbol of the stack
                initial_symbol_stack = extractSubsetFromLine(line, ",", "{")[0]
                
            elif first_character == 'F': # extract the final states
               final_states_set = extractSubsetFromLine(line, ",", "{")
               
               if final_states_set == ['']:
                   final_states_set = []
               
            elif first_character == '(': # read a transition
                transition_parts = line.split("->") # Separate both parts of the transition
                string_left = transition_parts[0].strip() # The left part if before ->, removing blank spaces
                string_left = string_left[1:-1] # The first and the last characters ('(' and ')') are removed

        
                """ The inital state is before the first comma, the input symbol is between both commmas,
                and the symbol of the top of the  stack is after the second comma """
                
                parts_transition = string_left.split(',')
                start_state = parts_transition[0]
                input_symbol = parts_transition[1]
                initial_top = parts_transition[2]
                
                string_right = transition_parts[1].strip() # The right part is after ->, removing blank spaces
                string_right = string_right[1:-1] # The first and the last characters ('{' and '}') are removed
                
                transition_pairs = string_right.split(";") # Each one of the pairs are separated by semicolons. 
                transition_tuples = []
        
                """ Now, for each transition tuple, read the state and the new top of the stack,
                separated by comma. The characters '(' and ')' are also skiped. """
                for pair in transition_pairs:
                    tuple_parts = pair.split(",")
                    transition_state = tuple_parts[0][1:]
                    new_top_stack = tuple_parts[1][:-1]
                    transition_tuple = (transition_state,new_top_stack)
                    transition_tuples.append(transition_tuple)
                    
                "Now, add the transition"
                
                transition = TransitionAutomatonStack(start_state, input_symbol, initial_top, transition_tuples)
                transitions.append(transition)
                
        automaton_stack = AutomatonStack(states, input_symbols, stack_symbols, transitions, initial_state, final_states_set, initial_symbol_stack)
        
        return automaton_stack
    
    """ Static method that creates a non-deterministic finite automaton
    given the path of a file.
    It reads the lines of the file and creates the automaton from such
    lines using the previous method. """
    
    @staticmethod
    def readAutomaton(path_file):
        file = open(path_file)
        lines = file.readlines()
        generated_automaton = AutomatonStack.__fromText(lines)
        
        return generated_automaton
    
    """ Method that writes an automaton in an output file """
    
    def writeAutomaton(self, path_file):
         file = open(path_file, 'w')
         
         """ Write the states  """
         
         states_set = self.getStatesSet()
         
         string_states = createStringList("Q",states_set,",")
         file.write(string_states + "\n")  
         
         """ Write the input symbols """
         
         input_symbols = self.getAlphabetSymbols()
         
         string_input_symbols = createStringList("A", input_symbols, ",")
         file.write(string_input_symbols + "\n")  
         
         """ Write the stack symbols """
         
         stack_symbols = self.getStackSymbols()
         
         string_stack_symbols =  createStringList("B", stack_symbols, ",")
         file.write(string_stack_symbols + "\n")  
         
         """ Write the initial state """
         initial_state = self.getInitialState()
         
         string_initial_state = createStringList("q0", [initial_state], ",")
         file.write(string_initial_state + "\n")  
         
         """ Write the initial stack symbol """
         initial_stack_symbol = self.getInitialSymbolStack()
         
         string_initial_stack_symbol = createStringList("Z0", [initial_stack_symbol], ",")
         file.write(string_initial_stack_symbol + "\n")  

         """ Write the final states """

         final_states_set = self.getFinalStates()
         
         string_final_states = createStringList("F",final_states_set,",")
         file.write(string_final_states + "\n")  
         
         """Write the transitions"""
         
         file.write("\n") # A blank line before the transitions
         
         transitions = self.getTransitions()
         
         for transition in transitions:
             start_state = transition.getInitialState()
             input_symbol = transition.getInputSymbol()
             initial_top = transition.getInitialTop()
             string_transition = "(" + start_state + "," + input_symbol + "," + initial_top + ")"
             
             string_transition = string_transition + " -> {"
             
             transition_tuples = transition.getTransitionTuples()
             
             for transition_tuple in transition_tuples:
                 string_transition = string_transition + "(" + transition_tuple[0] + "," + transition_tuple[1] + ");"           
            
             string_transition = string_transition[:-1] # Remove the last semicolon
             string_transition = string_transition + "}"
            
             file.write(string_transition + "\n")  

        
         file.close()
             
        
    """
    def __str__(self):
         print("States set \n")
         print(self.__states_set)
         print("Input symbols \n")
         print(self.__alphabet_symbols)
         print("Stack symbols \n")
         print(self.__stack_symbols)
         print("Initial state \n ")
         print(self.__initial_state)
         print("Final states \n")
         print(self.__final_states)
         print("Initial symbols stack \n")
         print(self.__initial_symbol_stack)
         print("Transitions \n")
         
         for transition in self.__transition_function:
             print("(" + transition.getInitialState() + "," + transition.getInitialState() + "," + transition.getInitialTop() + ") -> ")
             transition_tuples = transition.getTransitionTuples()
             
             for transition_tuple in transition_tuples:
                 print(transition_tuple[0] + "," + transition_tuple[1])
                 
    """
        
        
    """ Check the belonging of a word given an instantaneous configuration, constituted by
     a state, a content of the stack and the remaining part of the word to read. """
     
    def __checkbelongingConfiguration(self, current_state, current_word, current_stack):
        
        final_states = self.getFinalStates()
        length_word = len(current_word) 
        transitions = self.getTransitions()
        num_symbols_stack = len(current_stack)
        
        if num_symbols_stack > 0:
            current_top = current_stack[num_symbols_stack - 1]
            
        else:
            current_top = ""

        
        if length_word == 0: 
            """ Base case: if the word is empty, the current state is final (criterion of final states)
            or the stack is empty (criterion of stack empty), then return True. """
            
            if current_state in final_states or current_stack == []:
                return True
            
            
            """ If the word is empty but the stack is not empty, then check whether the symbols of the 
            stack can be extracted thorugh null transitions or can be ended in a final state. """ 
            
            for transition in transitions:
                initial_state_transition = transition.getInitialState()
                input_symbol = transition.getInputSymbol()
                input_top = transition.getInitialTop()
                
                if initial_state_transition == current_state and input_symbol == "" and input_top == current_top:
                    new_stack = current_stack.copy()                
                    transition_tuples = transition.getTransitionTuples()
                    
                    """For each transition tuple, check the belonging with the configuration associated
                    with the new stack and the transition state """
                    
                    for transition_tuple in transition_tuples:
                        new_top = transition_tuple[1]
                        transition_state = transition_tuple[0]
                        new_stack = current_stack.copy()
                        new_stack.pop()
                        
                        if not new_top == "":
                            for symbol in reversed(new_top):
                                new_stack.append(symbol)
                            
              
                        partial_belonging = self.__checkbelongingConfiguration(transition_state,"",new_stack)

                        if partial_belonging:
                            return True

            "If the stack cannot be emptied or can not be ended in a final state, then return False"
            return False
        
        else: 
            first_symbol = current_word[0]
            
            """ If the stack is empty and there are more symbols of the word, return False. """
            
            if num_symbols_stack == 0:
                return False
            
            current_top = current_stack[num_symbols_stack -1]
            
            if length_word > 1:
                remaining_word = current_word[1:]
            
            else:
                remaining_word = ""
                
            
            """ Go across the transitions. For each transition, check whether the initial state coincides
            with the current state, the initial top coincides with the current top, and the 
            input symbol is the empty chain or coincides with the first symbol of the word. """
            
            for transition in transitions:
                start_state = transition.getInitialState()
                initial_top = transition.getInitialTop()
                
                if start_state == current_state and initial_top == current_top:
                    input_symbol = transition.getInputSymbol()
                    
                    if input_symbol == first_symbol or input_symbol == "":
                        
                        """ Go across the transition tuples. """
                        
                        transition_tuples = transition.getTransitionTuples()
                        
                        for transition_tuple in transition_tuples:
                            transition_state = transition_tuple[0]
                            new_top = transition_tuple[1]
                        
                            """ Make a copy of the current stack and update the top, extracting
                            the last symbol and pushing the ones of the new top. """
                        
                            new_stack = current_stack.copy()
                            new_stack.pop()
                            
                        
                            if not new_top == "":
                                for symbol in reversed(new_top):
                                    new_stack.append(symbol)
                        
                                
                            """Now, check the belonging going to the new configuration. If such
                            a belonging is True, return True. If the input symbol is not the empty
                            chain, then removing the first symbol of the current word. """
                            
                            if input_symbol == "":
                                partial_belonging = self.__checkbelongingConfiguration(transition_state, current_word, new_stack)
                               
                        
                            else:
                                partial_belonging = self.__checkbelongingConfiguration(transition_state, remaining_word, new_stack)
            
                
                            if partial_belonging:
                                return True
            
            "If the belonging is not true for any transition, then return False. "
            return False
            
    """ Check whether a word can be acepted by the automaton with stack.
    For it, it employs the previous method with the initial configuration
    (initial state, the whole word and the initial symbol of the stack). """
    
    def checkBelonging(self, word):
        initial_state = self.getInitialState()
        initial_stack = [self.getInitialSymbolStack()]
        
        belonging = self.__checkbelongingConfiguration(initial_state, word, initial_stack)
        
        return belonging
    
    """ It computes the automaton that accepts the same languaje as the initial one 
    via the criterion of final states. """ 
    
    def equivalentAutomatonFinalStates(self):
        final_states = self.getFinalStates()
        
        """If the automaton uses the final states criterion, then return the same automaton. """
        
        if len(final_states) > 0:
            print("There are final states")
            print(final_states)
            return self
        
        states_set = self.getStatesSet()
        input_alphabet = self.getAlphabetSymbols()
        
        """Add two new states: q0n and qf. q0n is the new initial state and qf is a new final state. """
        
        new_initial_state = "q0n"
        new_final_state = "qf"

        final_states_set = self.getFinalStates()
        
        new_states_set = states_set + [new_initial_state, new_final_state]
        new_final_states_set = final_states_set + [new_final_state]
        
        """ Add a new symbol to the stack alphabet: Z0n. It is the new initial stack symbol. """
        
        stack_alphabet = self.getStackSymbols()
        new_initial_stack_symbol = "Z0n"
        new_stack_alphabet = stack_alphabet + [new_initial_stack_symbol]
        
        transitions = self.getTransitions()
        original_initial_state = self.getInitialState()
        original_initial_symbol_stack = self.getInitialSymbolStack()
        
        """Add the transition \delta(q0n,\epsilon,Z0n) = {(q0,Z0Z0n)}. """
        
        new_top_initial_transition = original_initial_symbol_stack + new_initial_stack_symbol
        transition_tuple_from_initial = (original_initial_state, new_top_initial_transition)
        transition_from_initial_state = TransitionAutomatonStack(new_initial_state,"", new_initial_stack_symbol, [transition_tuple_from_initial])
        
        new_transitions = [transition_from_initial_state]
        
        """For each state q \in Q, add a transition (q,\spsilon, Z0n) = {(qf, Z0n)} """
        transition_tuple_from_original = (new_final_state, new_initial_stack_symbol)
      
        for state in states_set:
            new_transition = TransitionAutomatonStack(state, "", new_initial_stack_symbol, [transition_tuple_from_original])
            new_transitions.append(new_transition)
        
        transitions_new_automaton = transitions + new_transitions
        
        automaton_final_states = AutomatonStack(new_states_set, input_alphabet, new_stack_alphabet, transitions_new_automaton, new_initial_state, new_final_states_set, new_initial_stack_symbol)
        
        return automaton_final_states
        
    """ It computes the automaton that accepts the same languaje as the initial one 
    via the criterion of empty stack. """ 
    
    def equivalentAutomatonEmptyStack(self):
        final_states = self.getFinalStates()
        
        """If the automaton uses the empty stack criterion, then return the same automaton. """
        
        if len(final_states) == 0:
            print("The automaton uses the criterion of empty stack.")
            return self
        
        states_set = self.getStatesSet()
        input_alphabet = self.getAlphabetSymbols()
        
        """Add two new states: q0n and qs. q0n is the new initial state. There are no final 
        states in the new automaton. """
        
        new_initial_state = "q0n"
        new_state = "qs"
        
        new_states_set = states_set + [new_initial_state,new_state]
        
        new_final_states_set = []
        
        """ Add a new symbol to the stack alphabet: Z0n. It is the new initial stack symbol. """
        
        stack_alphabet = self.getStackSymbols()
        new_initial_stack_symbol = "Z0n"
        new_stack_alphabet = stack_alphabet + [new_initial_stack_symbol]
                
        transitions = self.getTransitions()
        original_initial_state = self.getInitialState()
        original_initial_symbol_stack = self.getInitialSymbolStack()

        """Add the transition \delta(q0n,\epsilon,Z0n) = {(q0,Z0Z0n)}. """
        
        new_top_initial_transition = original_initial_symbol_stack + new_initial_stack_symbol
        transition_tuple_from_initial = (original_initial_state, new_top_initial_transition)
        transition_from_initial_state = TransitionAutomatonStack(new_initial_state,"", new_initial_stack_symbol, [transition_tuple_from_initial])
        
        new_transitions = [transition_from_initial_state]
        
        """ For each symbol H of the new stack alphabet, add a transition \delta (qs,\epsilon,H) = {(qs,\epsilon)}
        and, for each p final state, a transition \delta(p,\epsilon,H) = {(qs, H)} """
        
        transition_tuple_from_qs = (new_state, "")
        
        for stack_symbol in new_stack_alphabet:
            transition_from_qs = TransitionAutomatonStack(new_state, "", stack_symbol, [transition_tuple_from_qs])
            new_transitions.append(transition_from_qs)
            
            transition_tuple_from_final = (new_state, stack_symbol)

            for final_state in final_states:
                transition_from_qs = TransitionAutomatonStack(final_state ,"", stack_symbol, [transition_tuple_from_final])
                new_transitions.append(transition_from_qs)
                
        
        transitions_new_automaton = transitions + new_transitions
        
        automaton_empty_stack = AutomatonStack(new_states_set, input_alphabet, new_stack_alphabet, transitions_new_automaton, new_initial_state, new_final_states_set, new_initial_stack_symbol)
        
        return automaton_empty_stack
                
        
    """ It check whether the automaton is deterministic. """
        
    def isDeterministic(self):
        transitions = self.getTransitions()
        num_transitions = len(transitions)
        
        """ For each transition, check whether there is a unique transition tuple.
        In such a case, if the input symbol is the empty word, check whether there is 
        no another transition with the same input state and initial top. """
        
        for transition in transitions:
            transition_tuples = transition.getTransitionTuples()
            num_transition_tuples = len(transition_tuples)
            
            if num_transition_tuples > 1: # There are two or more transition tuples
                print("Deterministic broken due to more than one tuples")
                return False
            
            else:
                input_symbol = transition.getInputSymbol()
                
                if input_symbol == "":
                    
                    """Check whether there is another transition with the same start state,
                     an input symbol not equal to \epsilon and the same top of the stack. """
                    
                    start_state = transition.getInitialState()
                    initial_top = transition.getInitialTop()
                    
                    transition_found = False
                    i = 0
                    
                    while i < num_transitions and not transition_found:
                        start_state2 = transitions[i].getInitialState()
                        initial_top2 = transitions[i].getInitialTop()
                        input_symbol2 = transitions[i].getInputSymbol()
                        
                        if start_state2 == start_state and initial_top == initial_top2 and not input_symbol2 == "":
                            transition_found = True
                            print("Deterministic broken due to the transition")
                            print(start_state2)
                            print(input_symbol2)
                            print(initial_top2)
                            
                        else:
                            i = i+1
                    
                    if transition_found:
                        return False
                    
                
        "If all transitions verify the aforementioned condition, return True"
        return True
    
    """ It makes, for a state q, its copy (q,0), (q,1), or (q,2) for the deterministic automaton that 
    acepts the complementary languaje"""
    
    def __copyStateToComplementary(self, state, index):
        copy_state = "(" + state + "," + str(index) + ")"
        
        return copy_state
    
    """ It computes the deterministic automaton that accepts the complementay languaje.
    Remark that, to compute such an automaton, the original automaton must be deterministic. """
        
    def complementaryDeterministic(self):
        if not self.isDeterministic():
            print("The automaton must be deterministic")
            
        else:            
            states_set = self.getStatesSet()
            input_alphabet = self.getAlphabetSymbols()
            stack_alphabet = self.getStackSymbols()
            initial_symbol_stack = self.getInitialSymbolStack()
            initial_state = self.getInitialState()
            final_states_set = self.getFinalStates()
        
            """ For each state q make three copies: (q,0), (q,1), and (q,2) via the previous method.
            The final states are the ones of the form (q,2). """
        
            states_complementary_automaton = []
            final_states_complementary_automaton = []
            
            for state in states_set:
                for j in range(3):
                    state_complementary_automaton = self.__copyStateToComplementary(state, j)
                    states_complementary_automaton.append(state_complementary_automaton)
                    
                    if j == 2:
                        final_states_complementary_automaton.append(state_complementary_automaton)
                        
            """ The initial state of the complementary automaton is (q0,1) if q0 is final and (q0,0) otherwise. """
            
            if initial_state in final_states_set:
               initial_state_complementary_automaton = self.__copyStateToComplementary(initial_state, 1)
               
            else:
               initial_state_complementary_automaton = self.__copyStateToComplementary(initial_state, 0)

            """ Go across the transitions of the original automaton. """

            transitions = self.getTransitions()
            transitions_complementary_automaton = []
            
            for transition in transitions:
                initial_state_transition = transition.getInitialState() 
                initial_top = transition.getInitialTop()
                transition_tuple = transition.getTransitionTuples()[0]
                input_symbol = transition.getInputSymbol()
                
                copy_state0 = self.__copyStateToComplementary(initial_state_transition,0)
                copy_state1 = self.__copyStateToComplementary(initial_state_transition,1)
                
                if input_symbol == "":
                    
                    """ For each transition of the form \delta(q,\epsilon,X) = {(p,\alpha)}, add to the new automaton
                     \delta'((q,0), \epsilon, X) = \{((p,1),\alpha)\} if p \in F 
                     and \delta'((q,0), \epsilon, X) = \{((p,0),\alpha)\}$ if p \notin F
                     \delta'((q,1), \epsilon, X) = \{((p,1),\alpha)\}."""
                     
                    copy_transition_state1 = self.__copyStateToComplementary(transition_tuple[0],1)
                     
                    transition_tuple1 = (copy_transition_state1, transition_tuple[1])
                     
                    transition1 = TransitionAutomatonStack(copy_state1, "", initial_top, [transition_tuple1])
                     
                    if transition_tuple[0] in final_states_set:
                         transition_tuple2 = transition_tuple1
                         
                    else:
                         copy_transition_state0 = self.__copyStateToComplementary(transition_tuple[0],0)
                         transition_tuple2 = (copy_transition_state0, transition_tuple[1])
                         
                    transition2 = TransitionAutomatonStack(copy_state0, "", initial_top, [transition_tuple2])


                    transitions_complementary_automaton.append(transition1)
                    transitions_complementary_automaton.append(transition2)
     
                
                else:
                    
                    """ For each transition of the form \delta(q,a,X) = {(p,\alpha)}, add to the new automaton
                    \delta'((q,0), \epsilon, X) = {((q,2), X)}. Also, 
                    \delta'((q,1), a, X) = \{((p,0),\alpha)\}$ if p \notin F and
                    \delta'((q,1), a, X) = \{((p,1),\alpha)\}$ if p \in F """
                
                    copy_state2 = self.__copyStateToComplementary(initial_state_transition,2)
                    
                    transition_tuple1 = (copy_state2, initial_top)
                    
                    transition1 = TransitionAutomatonStack(copy_state0, "", initial_top, [transition_tuple1])

                    if transition_tuple[0] in final_states_set:
                        state_transition_tuples_23 = self.__copyStateToComplementary(transition_tuple[0],1) 
                        
                    else:
                        state_transition_tuples_23 = self.__copyStateToComplementary(transition_tuple[0],0) 

                
                    transition_tuples_23 = (state_transition_tuples_23, transition_tuple[1])
                    
                    transition2 = TransitionAutomatonStack(copy_state0, input_symbol, initial_top, [transition_tuples_23])
                    transition3 = TransitionAutomatonStack(copy_state1, input_symbol, initial_top, [transition_tuples_23])

                    transitions_complementary_automaton.append(transition1)
                    transitions_complementary_automaton.append(transition2)
                    transitions_complementary_automaton.append(transition3)

        complementary_automaton = AutomatonStack(states_complementary_automaton, input_alphabet, stack_alphabet, transitions_complementary_automaton, initial_state_complementary_automaton, final_states_complementary_automaton, initial_symbol_stack)
        
        return complementary_automaton
    
    """ It computes the state resulting from make a pair of states in the intersection automaton. """
    
    def __pairStatesIntersectionAutomaton(self, state1, state2):
        pair_states = "(" + state1 + "," + state2 + ")"
        
        return pair_states
    
    
    """ It returns the transition tuples from a state given a input symbol (that can also be the empty chain)
    and top of the stack. """
    
    def __getTransitionTuplesFromSymbolState(self, state, input_symbol, stack_symbol):    
        i = 0
        transitions = self.getTransitions()
        num_transitions = len(transitions)
        transition_found = False
        
        """ Look for a transition with that stack symbol, that input symbol and that state."""
        
        while i < num_transitions and not transition_found:
            initial_top_transition = transitions[i].getInitialTop()
            initial_state_transition = transitions[i].getInitialState()
            input_symbol_transition = transitions[i].getInputSymbol()
                        
            if initial_top_transition == stack_symbol and initial_state_transition == state and input_symbol_transition == input_symbol:
                transition_found = True
                transition_tuples = transitions[i].getTransitionTuples()
                        
            else:
                i = i+1
            
        
        if transition_found:
            return transition_tuples
        
        else:
            return []
        
    """ It computes the transition tuples composed by the pairs of states of the transition 
    tuples and a state of the DFA and the stack symbols"""
    
    def __makeTransitionTuples(self, transition_tuples, state_DFA):
        new_transition_tuples = []
        
        for transition_tuple in transition_tuples:
            pair_states_transition = self.__pairStatesIntersectionAutomaton(transition_tuple[0],state_DFA)
            new_transition_tuple = (pair_states_transition, transition_tuple[1]) 
            new_transition_tuples.append(new_transition_tuple) 
                  
        return new_transition_tuples
        
    
    """ It computes the automaton with stack that accepts the intersection of the languaje 
    acepted by the original automaton and the one acepted by a Deterministic Finite Automaton. 
    """
        
    def intersectionFiniteAutomaton(self, deterministic_finite_automaton):
        input_symbols = self.getAlphabetSymbols()
        input_symbols_DFA = deterministic_finite_automaton.getAlphabetSymbols()
        
        if not input_symbols == input_symbols_DFA:
            print("Both automatons must have the same input alphabet")
               
        else:
            states_stack_automaton = self.getStatesSet()
            states_DFA = deterministic_finite_automaton.getStatesSet()
            final_states_stack_automaton = self.getFinalStates()
            final_states_DFA = deterministic_finite_automaton.getFinalStates()
            stack_symbols = self.getStackSymbols()
            initial_symbol_stack = self.getInitialSymbolStack()
            
            
            """ The states of the intersection automaton are the pairs of states of the 
            automaton stack and the finite automaton, computed via the previous method. 
            The final states of the intersection automaton are the pairs of final states. """
            
            states_intersection = []
            final_states_intersection = []
            
            for state_stack in states_stack_automaton:
                for state_DFA in states_DFA:
                    state_intersection = self.__pairStatesIntersectionAutomaton(state_stack, state_DFA)
                    states_intersection.append(state_intersection)
                    
                    if state_stack in final_states_stack_automaton and state_DFA in final_states_DFA:
                        final_states_intersection.append(state_intersection)
        
                       
            """ The initial state of the intersection automaton is the pair composed of 
            the initial states of both automaton """
            
            initial_state_stack = self.getInitialState()
            initial_state_DFA = deterministic_finite_automaton.getInitialState()
            initial_state_intersection = self.__pairStatesIntersectionAutomaton(initial_state_stack, initial_state_DFA)
        
            transitions_DFA = deterministic_finite_automaton.getTransitionFunction()
            num_transitions_DFA = len(transitions_DFA)
            transitions_intersection = []
            
            for state_stack in states_stack_automaton:
                for stack_symbol in stack_symbols:
                    null_transition_found = False
                    i = 0
                    
                    """ Look for all the transition tuples (r,\alpha) = \delta(p,\epsilon,X).
                    If there is one or more tuples, add the corresponding transitions. """
                    
                    null_transition_tuples = self.__getTransitionTuplesFromSymbolState(state_stack, "", stack_symbol)
                    null_transition_found = len(null_transition_tuples) > 0
                    
                    for state_DFA in states_DFA:
                        
                        pair_states_initial = self.__pairStatesIntersectionAutomaton(state_stack,state_DFA)
                        
                        if null_transition_found:
                            transition_tuples_new_null = self.__makeTransitionTuples(null_transition_tuples,state_DFA)
                            new_null_transition = TransitionAutomatonStack(pair_states_initial, "", stack_symbol, transition_tuples_new_null)
                            transitions_intersection.append(new_null_transition)
                                
                        for symbol in input_symbols:
                            
                            """ Look for all the transition tuples (r,\alpha) = \delta(p,a,X). """
                            
                            transition_symbol_tuples = self.__getTransitionTuplesFromSymbolState(state_stack, symbol, stack_symbol)
                            transition_stack_found = len(transition_symbol_tuples) > 0
                                   
                            if transition_stack_found:
                                """ If there is one or more transition tuples, then look for the state s
                                such that s = \delta'(q,a). """
                                
                                transition_state_DFA_found = False
                                i = 0
                                    
                                while i < num_transitions_DFA and not transition_state_DFA_found:
                                    initial_state_transition = transitions_DFA[i].getInitialState()
                                    input_symbol_transition = transitions_DFA[i].getInputSymbol() 
                                        
                                    if initial_state_transition  == state_DFA and input_symbol_transition == symbol:
                                        transition_state_DFA_found = True
                                        transition_state_DFA = transitions_DFA[i].getFinalStates()[0]
                                    
                                    else:
                                        i = i+1
                                
                                """ Add the transition tuples \delta''((p,q), a, X) = ((r,s), \alpha), 
                                for each (r,\alpha) = \delta(p,a,X). """
                                
                                new_transition_tuples = self.__makeTransitionTuples(transition_symbol_tuples,transition_state_DFA)
                                new_transition = TransitionAutomatonStack(pair_states_initial, symbol, stack_symbol, new_transition_tuples)
                                transitions_intersection.append(new_transition)

        intersection_automaton = AutomatonStack(states_intersection, input_symbols, stack_symbols, transitions_intersection, initial_state_intersection, final_states_intersection, initial_symbol_stack)
        
        return intersection_automaton
