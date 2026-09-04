# -*- coding: utf-8 -*-

from typing import AbstractSet
from TransitionFunction import Transition
from Utils import extractSubsetFromLine, getPowerset
import networkx as nx
import graphviz as pgv

"""
Class for Non-deterministic Finite Automatons
"""
alphabet_symbols_type = str # type of symbols of input alphabet
states_type = str # type of the states of the automaton




class FiniteAutomaton:
    __states_set: AbstractSet[states_type] # The set of states of the automaton
    __alphabet_symbols: AbstractSet[alphabet_symbols_type] # The input alphabet
    __transition_function: AbstractSet[Transition] # The transition function
    __initial_state: states_type # The initial state 
    __final_states: AbstractSet[states_type] # The set of final states 
    
    """ The constructor of the class. It initializes the attributes and validates
    the initial and final states and the transition function """
    
    def __init__(self, states, input_alphabet, transitions, initial, final_set) -> None:
        self.__states_set = states
        self.__alphabet_symbols = input_alphabet
        self.__initial_state = initial
        self.__transition_function = transitions
        self.__final_states = final_set
        
    """ Get and Set methods """
        
    def getStatesSet(self):
        return self.__states_set
    
    def getAlphabetSymbols(self):
        return self.__alphabet_symbols
    
    def getInitialState(self):
        return self.__initial_state
    
    def getTransitionFunction(self):
        return self.__transition_function
    
    def getFinalStates(self):
        return self.__final_states
    
    def setStatesSet(self, states_set):
        self.__states_set = states_set
    
    def setAlphabetSymbols(self, input_alphabet):
        self.__alphabet_symbols = input_alphabet
    
    def setInitialState(self, initial_state):
        self.__initial_state = initial_state
    
    def setTransitionFunction(self, transitions):
        self.__transition_function = transitions
    
    def setFinalStates(self, final_states):
        self.__final_states = final_states

    def _normalize_symbols(self, symbols):
        if isinstance(symbols, str):
            return [item.strip() for item in symbols.split(",") if item.strip()]
        return [item for item in symbols if item]

    def _as_unique_list(self, values):
        result = []
        for value in values:
            if value not in result:
                result.append(value)
        return result

    def _set_states(self, states):
        unique_states = self._as_unique_list(states)
        if isinstance(self.__states_set, set):
            self.__states_set = set(unique_states)
        else:
            self.__states_set = unique_states

    def _set_alphabet(self, alphabet):
        unique_alphabet = self._as_unique_list(alphabet)
        if isinstance(self.__alphabet_symbols, set):
            self.__alphabet_symbols = set(unique_alphabet)
        else:
            self.__alphabet_symbols = unique_alphabet

    def _set_final_states(self, final_states):
        unique_finals = self._as_unique_list(final_states)
        if isinstance(self.__final_states, set):
            self.__final_states = set(unique_finals)
        else:
            self.__final_states = unique_finals

    def _get_transition_list(self):
        if isinstance(self.__transition_function, list):
            return self.__transition_function
        if isinstance(self.__transition_function, set):
            return list(self.__transition_function)
        return list(self.__transition_function)

    def _set_transition_list(self, transitions):
        cleaned = self._as_unique_list(transitions)
        if isinstance(self.__transition_function, set):
            self.__transition_function = set(cleaned)
        else:
            self.__transition_function = cleaned
                
    
    """ Methods to modify states and transitions dynamically """
    
    def add_state(self, state_name):
        """Adds a new state to the automaton"""
        if state_name not in self.__states_set:
            states = self._as_unique_list(list(self.__states_set) + [state_name])
            self._set_states(states)
    
    def add_transition(self, from_state, symbol, to_state):
        """Adds a new transition to the automaton"""
        self.add_state(from_state)
        self.add_state(to_state)

        if symbol not in self.__alphabet_symbols:
            alphabet = self._as_unique_list(list(self.__alphabet_symbols) + [symbol])
            self._set_alphabet(alphabet)
        
        # Check if transition already exists
        transitions = self._get_transition_list()
        transition_exists = False
        for transition in transitions:
            if (transition.getInitialState() == from_state and 
                transition.getInputSymbol() == symbol):
                # Add to existing transition's final states
                if to_state not in transition.getFinalStates():
                    transition.getFinalStates().append(to_state)
                transition_exists = True
                break
        
        if not transition_exists:
            # Create new transition
            new_transition = Transition(from_state, symbol, [to_state])
            transitions.append(new_transition)

        self._set_transition_list(transitions)
    
    def set_state_as_initial(self, state):
        """Sets a state as the initial state of the automaton"""
        if state not in self.__states_set:
            self.add_state(state)
        self.__initial_state = state
    
    def set_state_as_final(self, state):
        """Adds a state to the set of final states"""
        if state not in self.__states_set:
            self.add_state(state)
        if state not in self.__final_states:
            final_states = self._as_unique_list(list(self.__final_states) + [state])
            self._set_final_states(final_states)
    
    def set_state_as_regular(self, state):
        """Removes initial/final properties from a state (makes it regular)"""
        if state in self.__final_states:
            new_finals = [final_state for final_state in self.__final_states if final_state != state]
            self._set_final_states(new_finals)
        if self.__initial_state == state:
            self.__initial_state = None

    def remove_state(self, state):
        """Removes a state and its related transitions"""
        if state not in self.__states_set:
            return

        self._set_states([s for s in self.__states_set if s != state])
        self._set_final_states([s for s in self.__final_states if s != state])

        if self.__initial_state == state:
            self.__initial_state = None

        transitions = []
        for transition in self._get_transition_list():
            if transition.getInitialState() == state:
                continue

            remaining_targets = [target for target in transition.getFinalStates() if target != state]
            if remaining_targets:
                transition.setFinalStates(remaining_targets)
                transitions.append(transition)

        self._set_transition_list(transitions)

    def remove_transition(self, from_state, symbol, to_state=None):
        """Removes a transition or one specific destination"""
        transitions = []
        for transition in self._get_transition_list():
            is_same_transition = (
                transition.getInitialState() == from_state
                and transition.getInputSymbol() == symbol
            )

            if not is_same_transition:
                transitions.append(transition)
                continue

            if to_state is None:
                continue

            remaining_targets = [target for target in transition.getFinalStates() if target != to_state]
            if remaining_targets:
                transition.setFinalStates(remaining_targets)
                transitions.append(transition)

        self._set_transition_list(transitions)

    def update_transition_symbols(self, from_state, to_state, symbols):
        """Replaces all symbols used from one state to another"""
        symbol_list = self._normalize_symbols(symbols)

        transitions = []
        for transition in self._get_transition_list():
            if transition.getInitialState() != from_state:
                transitions.append(transition)
                continue

            remaining_targets = [target for target in transition.getFinalStates() if target != to_state]
            if remaining_targets:
                transition.setFinalStates(remaining_targets)
                transitions.append(transition)

        self._set_transition_list(transitions)

        for symbol in symbol_list:
            self.add_transition(from_state, symbol, to_state)

    def to_dict(self):
        """Exports the automaton model as a serializable dictionary"""
        transitions = []
        for transition in self._get_transition_list():
            transitions.append(
                {
                    "from": transition.getInitialState(),
                    "symbol": transition.getInputSymbol(),
                    "to": list(transition.getFinalStates()),
                }
            )

        return {
            "states": list(self.__states_set),
            "alphabet": list(self.__alphabet_symbols),
            "initial": self.__initial_state,
            "final": list(self.__final_states),
            "transitions": transitions,
        }

    def from_dict(self, model):
        """Loads the automaton model from a dictionary"""
        states = model.get("states", [])
        alphabet = model.get("alphabet", [])
        initial = model.get("initial")
        final_states = model.get("final", [])

        transitions = []
        for transition_data in model.get("transitions", []):
            start_state = transition_data.get("from")
            input_symbol = transition_data.get("symbol")
            final_targets = transition_data.get("to", [])
            transitions.append(Transition(start_state, input_symbol, list(final_targets)))

        self._set_states(states)
        self._set_alphabet(alphabet)
        self._set_final_states(final_states)
        self.__initial_state = initial
        self._set_transition_list(transitions)
        
    """It validates the transition function by checking that all transitions are right.
    A transition is correct if, and only if, the initial and final states belong to 
    the states set and the input belongs to the input alphabet """    
        
    # def _validateTransitionFunction(self):

    """ It validates the initial state by cheking that it belongs to the states set """

    # def _validateInitialState(self):

    """It validates the set of final states by cheking that all states of that set belong
    to the states set of the automaton"""

    # def _validateFinalStates(self): 
        
        
    """ Static method that creates a non-deterministic finite automaton
    from a list of strings. """    
        
    @staticmethod
    def __fromText(lines): 
        transitions = []
        
        """ Obtain the list of states, input symbols, final states, transitions
        and initial state. The list to obtain depends on the first character 
        of the line. """
        
        for line in lines:
            first_character = line[0]
            
            if first_character == 'Q': # extract the states, assuming that the initial state is the first one
               states = extractSubsetFromLine(line, ",", "{")
               initial_state = states[0]
                        
            elif first_character == 'A': # extract the input symbols
                input_symbols = extractSubsetFromLine(line, ",", "{")
                
            elif first_character == 'F': # extract the final states
               final_states_set =  extractSubsetFromLine(line, ",", "{")
               
                    
            elif first_character == '(': # read a transition
                transition_parts = line.split("->") # Separate both parts of the transition
                string_left = transition_parts[0].strip() # The left part if before ->, removing blank spaces
                string_left = string_left[1:-1] # The first and the last characters ('(' and ')') are removed
               
                "The inital state is before the comma, and the input symbol after the comma"
                parts_transition = string_left.split(',')
                start_state = parts_transition[0]
                input_symbol = parts_transition[1]
        
                string_right = transition_parts[1].strip() # The right part is after ->, removing blank spaces
                string_right = string_right[1:-1] # The first and the last characters ('{' and '}') are removed
                states_transition = string_right.split(",")
                final_states_transition = []
                
                for i in range(len(states_transition)):
                    final_states_transition.append(states_transition[i])
                    
                transition = Transition(start_state, input_symbol, final_states_transition)
                transitions.append(transition)
                    
                    
        generated_automaton = FiniteAutomaton(states, input_symbols, transitions, initial_state, final_states_set)
        
        return generated_automaton
    
    """
    Static method that creates a non-deterministic finite automaton
    given the path of a file.
    It reads the lines of the file and creates the automaton from such
    lines using the previous method.
    """
    
    @staticmethod
    def readAutomaton(path_file):
        file = open(path_file)
        lines = file.readlines()
        generated_automaton = FiniteAutomaton.__fromText(lines)
        
        return generated_automaton
                       
    
    """ It shows the directed graph corresponding to the automaton """   
       
    def showAutomaton(self, path_transition_diagram=None) -> None:
        graph = pgv.Digraph()
        
        states_set = self.getStatesSet()
        final_states = self.getFinalStates()
        

        for state in states_set :
            if state in final_states:
                shape_node = 'doublecircle'
                
            else:
                shape_node = 'circle'
             
            graph.node(state, shape = shape_node)
            
        initial_node = "I"
        graph.node(initial_node, shape = 'plaintext')
        
        graph.edge(initial_node, self.getInitialState())
        
        edges = []  
        label_edges = []
        
        transitions = self.getTransitionFunction()
            
        for transition in  transitions:
            set_final_states = transition.getFinalStates()
            initial_state = transition.getInitialState()
            input_symbol = transition.getInputSymbol()
            
            for transition_state in set_final_states:
                edge = (initial_state, transition_state)
                
                if edge not in edges:
                    edges.append(edge)
                    label_edges.append(input_symbol)
                    
                else:
                    index_edge = edges.index(edge) # Obtain the index of the edge in the list 
                    label_edges[index_edge] = label_edges[index_edge] + "," + input_symbol 
        
        
        for i in range(len(edges)):
            graph.edge(edges[i][0], edges[i][1], label = label_edges[i])
        
        if path_transition_diagram is None:
            graph.render(view = True)
        else:
            graph.render(path_transition_diagram, view = True)
   
    
    """ It computes the transition state given a initial state and an input symbol """    
         
    def __stateTransition(self, symbol, input_state):
        transitions = self.getTransitionFunction()
        transition_found = False
        num_transitions = len(transitions)
        state_transition = None  # FIX: well-defined default instead of UnboundLocalError
        i = 0
        
        while i < num_transitions and not transition_found:
            input_symbol = transitions[i].getInputSymbol()
            initial_state = transitions[i].getInitialState()
            
            if input_symbol == symbol and initial_state == input_state:
                state_transition = transitions[i].getFinalStates()[0]
                transition_found = True
            
            else:
                i+=1
                
        return state_transition
    
        
    """ It determines the \delta^{*} function given a subset of states B and a symbol a.
    Remark that this function is defined as \delta^{*}(B,a) = \cup_{q \in B}\delta(q,a) """    
        
    def _delta_star_symbol(self, subset_states, symbol):
        set_states_transition = []
        transitions = self.getTransitionFunction()
        
        for state in subset_states:
            transition_found = False
            i = 0
            num_transitions =  len(transitions)
            
            "Find the transition such that the initial state is p and the input symbol is a"
            while not transition_found and i < num_transitions:
                initial_state = transitions[i].getInitialState()
                input_symbol = transitions[i].getInputSymbol()
                
                if initial_state == state and input_symbol == symbol:
                    set_final_states = transitions[i].getFinalStates()
                    
                    "Between the states that we can move, add the ones not included "
                    for state_transition in set_final_states:
                        if state_transition not in set_states_transition:
                            set_states_transition.append(state_transition)
                    
                    transition_found = True
                
                else:
                    i = i+1
        
        return set_states_transition
    
    """ It determines the It determines the \delta^{*} function given a subset of states B and a word u.
    Remark that this function is defined as follows: \delta^{*}(B, \epsilon) = B 
    \delta^{*}(B, au) = \delta^{*}(\delta^{*}(B, a),u)) """
    
    def __delta_star_word(self, subset_states, word):
        
        if len(word) == 0: # Base case: if the word is \epsilon, return B
            return subset_states
        
        else: # Recursive case: the word has one or more symbols
            first_symbol = word[0]
            remaining_word = word[1:]
            subset_first_symbol = self._delta_star_symbol(subset_states, first_symbol) # \delta^{*}(B, a)
            set_states_transition = self.__delta_star_word(subset_first_symbol, remaining_word) # \delta^{*}(\delta^{*}(B, a),u))
    
            return set_states_transition
        
    """ It checks whether the states set of a transition contains a final state. """
    
    def _finalIncluded(self, states_transition):
        num_states_transition = len(states_transition)
        i = 0
        final_states = self.getFinalStates()
        final_state_found = False
        
        "Find a final state"
        while i < num_states_transition and not final_state_found:
            if states_transition[i] in final_states:
                final_state_found = True
            
            else:
                i = i+1
                
        return final_state_found

        
    
    """ It checks whether a word u is accepted by the finite automaton. It happens if, and only if
    \delta^{*}({qo}, u) contains at least one final state"""    
        
    def wordBelongs(self, word) -> bool:
        initial_state = self.getInitialState()           
        set_initial_state = [initial_state]
        states_transition = self.__delta_star_word(set_initial_state, word)
                
        final_state_found = self._finalIncluded(states_transition)
        
        return final_state_found
        
    """ It checks whether the automaton is deterministic. It happens if, and only if,
    for each state and input symbol, there is a transition whose set of output states is singleton """   
        
    def deterministicAutomaton(self) -> bool:
        states_set = self.getStatesSet()
        alphabet_symbols = self.getAlphabetSymbols()
        transitions = self.getTransitionFunction()
        num_transitions = len(transitions)

        # If there are epsilon (empty) transitions present, automaton is not deterministic
        for tr in transitions:
            inp = tr.getInputSymbol()
            if inp is None or str(inp).strip() == "":
                return False
     
        """For each state p and input symbol a, look for a transition with initial state p and symbol a"""
        for state in states_set:
            for symbol in alphabet_symbols:
                transition_found = False
                i = 0
                
                while not transition_found and i < num_transitions:
                    initial_state_transition = transitions[i].getInitialState()
                    input_symbol = transitions[i].getInputSymbol()
                    
                    if initial_state_transition == state and input_symbol == symbol:
                        final_states_transition = transitions[i].getFinalStates()
                        
                        if not len(final_states_transition) == 1: # When the transition is found, check whether there is a unique transition state
                            return False
                        
                        transition_found = True
                        
                    else:
                        i = i+1
                
                if not transition_found: # If there is no transition for p and a, return False
                    return False
        
        "If, for each state and input symbol there is a unique transition, return True"
        return True
        
    """ It returns the state of the deterministic automaton corresponding to a subset of states
    of the non-deterministic automaton. For example, {q1,q2,...,qn} corresponds to the state 
    (q1,q2,...,qn)
    """
    def _correspondenceDeterministic(self, subset):
        num_elements = len(subset)
        
        if num_elements == 0: # The subset associated with the empty set
            return ""
        
        elif num_elements == 1: # A singleton subset
            return subset[0]
            
        else:
            corresponding_state = ""
            states_set = self.getStatesSet()
            
            """For each state in the set of states, check whether that state is in the subset"""
            for state in states_set:
                if state in subset:
                    if corresponding_state == "": # If p is the first state, the corresponding subset starts by p
                        corresponding_state = state
                            
                    else: # If it is not the first state, add ,p
                        corresponding_state +="," + state
            
            return corresponding_state
    
    """It finds the deterministic automaton corresponding to the automaton"""
        
    def transformDeterministic(self):
         deterministic = self.deterministicAutomaton()
                 
         if deterministic: # If the automaton is deterministic, there is no conversion to do 
             return self
         
         else:
             """Obtain the power set of the set of states of the original automaton. For each
            subset of states, obtain the corresponding state via the previous function. """
            
             states_set = self.getStatesSet()
             initial_state = self.getInitialState()
             final_states = self.getFinalStates()
             power_set_states = getPowerset(states_set)
             
             states_deterministic_automaton = []
             final_states_deterministic_automaton = []
            
             
             for subset in power_set_states:
                corresponding_state = self._correspondenceDeterministic(subset)
                states_deterministic_automaton.append(corresponding_state)
                num_states = len(subset)

                """ If the subset has a unique state and such an state is the initial one of the 
                non-deterministic automaton, then the corresponding subset is the initial state
                of the deterministic automaton. """
                                
                if num_states == 1 and subset[0] == initial_state:
                    initial_state_deterministic_automaton = corresponding_state
             
                """ If there is a set in the subset that is a final state of the non-deterministic
                automaton, then the corresponding subset is a final state of the deterministic automaton.
                """
                
                final_found = False
                i = 0
                
                while i < num_states and not final_found:
                    if subset[i] in final_states:
                        final_found = True
                        
                    else:
                        i = i+1
                        
                if final_found:
                    final_states_deterministic_automaton.append(corresponding_state)
            
             """Now, add the transitions of the deterministic automaton. For each subset B and 
             input symbol a, determine \delta^{*}(B,a) and compute the corresponding set. That tuple
             of three elements determine the transition
             """
            
             transitions_deterministic = []
             alphabet_symbols = self.getAlphabetSymbols()

             for subset in power_set_states:
                 corresponding_input_state = self._correspondenceDeterministic(subset)
                 
                 for symbol in alphabet_symbols:
                     states_transition = self._delta_star_symbol(subset,symbol)
                     corresponding_state_transition = self._correspondenceDeterministic(states_transition)
                 
                     transition_deterministic = Transition(corresponding_input_state, symbol, [corresponding_state_transition])
                     transitions_deterministic.append(transition_deterministic)
                
             "Now, the deterministic automaton can be generated"
             deterministic_automaton = FiniteAutomaton(states_deterministic_automaton, alphabet_symbols, transitions_deterministic, initial_state_deterministic_automaton, final_states_deterministic_automaton)
        
             return deterministic_automaton
    
    """ It computes the automaton that accepts the complementary language.
    For it, the automaton is transformed to deterministic and the set of final
    states is the complementary of the one of the original automaton. """    
        
    def complementaryAutomaton(self): 
         deterministic_automaton = self.transformDeterministic()
         complementary_final_set = []
         states_deterministic = deterministic_automaton.getStatesSet()
         initial_state_deterministic = deterministic_automaton.getInitialState()
         final_states_deterministic = deterministic_automaton.getFinalStates()
         transitions_deterministic = deterministic_automaton.getTransitionFunction()
         alphabet_symbols = self.getAlphabetSymbols()
         
         for state in states_deterministic:
             if state not in final_states_deterministic:
                 complementary_final_set.append(state)
                         
         complementary_automaton = FiniteAutomaton(states_deterministic, alphabet_symbols, transitions_deterministic, initial_state_deterministic, complementary_final_set)
         
         return complementary_automaton
     

    """ It computes the product automaton of the original automaton and a second one.
    It can be computes for both the intersection of the union. """
        
    def productAutomaton(self, second_automaton, union): 
         alphabet_symbols = self.getAlphabetSymbols()

         """ FIX: both automatons must share the same input alphabet for the
         product construction to make sense; fail with a clear, explicit None
         instead of silently using only self's alphabet and crashing later. """
         if set(alphabet_symbols) != set(second_automaton.getAlphabetSymbols()):
             print("Both automatons must have the same input alphabet")
             return None

         
         """ Firstly, we transform both automatons to deterministic """
         deterministic_self = self.transformDeterministic()
         deterministic_second = second_automaton.transformDeterministic()

         
         """ Compute the states set of the product automaton. It is composed of pairs (p,q),
         where p is a state of the first automaton and q is a state of the second one. """
         states_product_automaton = []
         final_states_product = []
         states_set_self = deterministic_self.getStatesSet()
         states_set_second = deterministic_second.getStatesSet()
         initial_self = deterministic_self.getInitialState()
         initial_second = deterministic_second.getInitialState()
         final_states_self = deterministic_self.getFinalStates()
         final_states_second = deterministic_second.getFinalStates()
         
         for state_first in states_set_self:
             for state_second in states_set_second:
                 state_product_automaton = state_first + "," +  state_second
                 states_product_automaton.append(state_product_automaton)
                 
                 
                 """Check whether it is the initial state of the product automaton, that is, 
                 the pair of initial states of both automatons """
                 if state_first == initial_self and state_second == initial_second:
                     initial_state_product = state_product_automaton
                     
                 """ If both states are final, then the state of the product automaton is also final.
                     If only one of the states is final, then the state of the product 
                     automaton is final only in case of union. """    
                 if state_first in final_states_self and state_second in final_states_second:
                     final_states_product.append(state_product_automaton)
                         
                 elif union:
                    if state_first in final_states_self or state_second in final_states_second:
                     final_states_product.append(state_product_automaton)
         
         """ Compute the transitions of the product automaton. For each pair (p,q) and input symbol a,
         the transition will be the pair composed of the transition of p and the transition of q
         with that symbol """
         
         
         transitions_product = []
            
         for symbol in alphabet_symbols:   
             for state_first in states_set_self:
                 state_transition_first = deterministic_self.__stateTransition(symbol, state_first)

                 for state_second in  states_set_second:
                     state_transition_second = deterministic_second.__stateTransition(symbol, state_second)
                         
                     start_state_product = state_first + "," + state_second  
                     state_transition_product = state_transition_first + "," + state_transition_second
                                          
                     transition_product = Transition(start_state_product, symbol, [state_transition_product])
                     transitions_product.append(transition_product)
             
         product_automaton = FiniteAutomaton(states_product_automaton, alphabet_symbols, transitions_product, initial_state_product,  final_states_product)
    
         return product_automaton
        
    """It computes the intersection automaton of the original automaton and a second one.
    For this, the product automaton with the union option in False is computed via the previous method"""    
        
    def intersectionAutomaton(self, second_automaton): 
        intersection_automaton = self.productAutomaton(second_automaton, False)
        
        return intersection_automaton
    
    """It computes the intersection automaton of the original automaton and a second one.
    For this, the product automaton with the union option in True is computed via the previous method"""    
        
    def unionAutomaton(self, second_automaton): 
        union_automaton = self.productAutomaton(second_automaton, True)
        
        return union_automaton
    
    """It removes a state from the automaton. Specifically, it removes the transitions such that the 
    initial state or one of the final states coincide with it, the state of the list of final 
    states  if it is final, and the state is finally removed from the list.  """
    
    def __delete_state(self, state):
        # Rebuild transitions excluding the deleted state as source
        # and removing the deleted state from transitions' target lists.
        new_transitions = []
        # iterate over a snapshot of transition list to avoid mutation issues
        for transition in list(self._get_transition_list()):
            # drop transitions that originate at the deleted state
            if transition.getInitialState() == state:
                continue

            # remove the deleted state from the transition target list
            remaining_targets = [t for t in transition.getFinalStates() if t != state]
            if remaining_targets:
                transition.setFinalStates(remaining_targets)
                new_transitions.append(transition)
            # if no remaining targets, drop the transition entirely

        self._set_transition_list(new_transitions)

        # remove state from final states if present
        if state in (self.getFinalStates() or []):
            remaining_finals = [s for s in self.getFinalStates() if s != state]
            self._set_final_states(remaining_finals)

        # finally, remove the state from the set of states
        states_list = list(self.getStatesSet()) if isinstance(self.getStatesSet(), (list, tuple)) else list(self.getStatesSet())
        if state in states_list:
            states_list = [s for s in states_list if s != state]
            self._set_states(states_list)
    
    """ It deletes the states not included in a subset of states"""
    
    def _deleteStatesNotIncluded(self, subset_states):
        # Iterate over a copy of the states list so deletions don't mutate the
        # sequence we're iterating and cause an infinite loop.
        for state in list(self.getStatesSet()):
            if state not in subset_states:
                self.__delete_state(state)
        
    
    """ It deletes the inaccessible states of the automaton by a recursive 
    search from the initial state """
    
    def deleteInaccessibleStates(self) -> None:
        initial_state = self.getInitialState()
        transitions = self.getTransitionFunction()
        accessible_states = [initial_state]
        states_to_explore = [initial_state]
        
        while len(states_to_explore) >= 1: # While there are states to explore
            "Extract the first state to explore"
            state_to_explore = states_to_explore[0]
            states_to_explore.remove(state_to_explore)
            
            """ Go across the transitions. For each transition with initial state 
            equal to the state to explore, put the transition states in the set of
            accessible states if they have not been included yet. """
            
            for transition in transitions: 
                initial_state_transition = transition.getInitialState()
                
                if initial_state_transition == state_to_explore:
                    final_states_transition = transition.getFinalStates()
                    
                    for transition_state in final_states_transition:
                        if transition_state not in accessible_states:
                            accessible_states.append(transition_state)
                            states_to_explore.append(transition_state)
        
        
        "Remove the states not included in the accessible states set"
        
        self._deleteStatesNotIncluded(accessible_states)
        
        
    """It checks whether the languaje accepted by an automaton if empty. 
    For this, the inaccesible states are removed via the previous method 
    and it is checked that there are final states after it """
        
    def emptyLanguaje(self) -> bool:
         self.deleteInaccessibleStates()
         empty_languaje = len(self.getFinalStates()) == 0
        
         return empty_languaje
    
    """ It deletes the error states, that is, 
    states from which a final state cannot be reached. 
    We go across the transitions in opposite sense starting from the final states. """    
    
    def deleteErrorStates(self) -> None:
        final_states = self.getFinalStates()
        transitions = self.getTransitionFunction()
        states_endable_final = []
        states_to_explore = []
        
        for final_state in final_states:
            states_to_explore.append(final_state)
            states_endable_final.append(final_state)
        
        while len(states_to_explore) >= 1: # While there are states to explore
            "Extract the first state to explore"
            state_to_explore = states_to_explore [0]
            states_to_explore.remove(state_to_explore)
            
            """Go across the transitions. For each transition such that the state  to explore
            belongs to the set of final states of the transition, add the initial state in the 
            set of enable final states if it has not been already included yet. """
            
            for transition in transitions:   
                final_states_transition = transition.getFinalStates()
               
                if state_to_explore in final_states_transition:
                   initial_state_transition = transition.getInitialState() 
                    
                   if initial_state_transition not in states_endable_final:
                       states_endable_final.append(initial_state_transition)
                       states_to_explore.append(initial_state_transition)
                    
        
        "Remove the states from which a final state cannot be reached "
        self._deleteStatesNotIncluded(states_endable_final)
        
        
    """ It checks whether the languje accepted by the automaton is finite.
    The inaccessible states, as well as the error states, are deleted. 
    Then, it checks whether the resulting graph is acyclic """
      
    def infiniteLanguaje(self) -> bool:
        
        "Delete the inaccesible and error states"
        self.deleteInaccessibleStates()
        self.deleteErrorStates() 
        
        "Construct the graph corresponding to the automaton "
        graph = nx.DiGraph()
         
        graph.add_nodes_from(self.getStatesSet()) # Copy the nodes from the states
        
        """Add the edges of the graph. For each transition \delta(p,a) = q, 
        add an arc from p to q if such an arc does not exist"""
        
        transitions = self.getTransitionFunction()
        
        for transition in transitions:
            initial_state_transition = transition.getInitialState()
            final_states_transition = transition.getFinalStates()

            for transition_state in final_states_transition:
               graph.add_edge(initial_state_transition, transition_state)
            
        # The languaje is infinity if, and only if, there is at least one cycle
        cycles = nx.recursive_simple_cycles(graph)
        infinity = len(cycles) > 0
        
        return infinity
      
    """ It checks whether the automaton M1 accepts the same languaje as a second 
    automaton M2. For this, the automaton that accepts
    L(M1) \cap L(M2)^c \cup L(M1)^c \cap L(M2).
    Then, it is checked whether the languaje accepted by this automaton is empty. """
     
    def sameLanguaje(self, second_automaton) -> bool:
      "First, we transform both automatons to deterministic"
      deterministic_self = self.transformDeterministic()
      deterministic_second = second_automaton.transformDeterministic()
      
      "Now, we obtain the complementary automatons" 
      
      complementary_self = deterministic_self.complementaryAutomaton()
      complementary_second = deterministic_second.complementaryAutomaton()

      "Compute M1 \cap \overline{M2} and  \overline{M1} \cap M2"
        
      self_second_complementary =  deterministic_self.intersectionAutomaton(complementary_second)
      self_complementary_second = deterministic_second.intersectionAutomaton(complementary_self)
      
      """ Now, compute the union of the two previous automatons and check whether the 
      accepted language is empty. """
      
      automaton_not_equality = self_second_complementary.unionAutomaton(self_complementary_second)
      same_languaje = automaton_not_equality.emptyLanguaje()
      
      return same_languaje
  
    """
    Method that recursively marks a pair of states as indistinguisable and,
    recursively, all pairs in the list associated. 
    """
    
    def __recursivelyMarkPairsStates(self, indistinguisable_states, i, j, lists_associated_states):
        indistinguisable_states[i][j] = False
        
        for pair_states in lists_associated_states[i][j]:
            if indistinguisable_states[pair_states[0]][pair_states[1]]:
               indistinguisable_states = self.__recursivelyMarkPairsStates(indistinguisable_states, pair_states[0], pair_states[1], lists_associated_states)
            
            
        return indistinguisable_states
      
    """ It computes the groups of indisguishable states of the automaton. 
    Basic condition: If p is final and q is not final: (p,q) is distinguishable
    Recursive condition:  If (p,q) is distinguisable, then (\delta(p,a), \delta(p,a))
    is indistinghisable for each input symbol a. 
    """
    
    def computeGroupsIndistinguishableStates(self):
        states_set = self.getStatesSet()
        transitions = self.getTransitionFunction()
        final_states = self.getFinalStates()
        alphabet_symbols = self.getAlphabetSymbols()
        
        num_states = len(states_set)
        num_transitions = len(transitions)
        indistinguisable_states = [] # list of list of boolean values. The value of i, j is true if the states i and j are indistinguisable. 
        lists_associated_states = [] # List of pairs associated with p_i, p_j
        
        """
        Initialize the lists of associated states and the list of boolean values for each pair of states.
        For the pair q_i, q_j, if both p_i and p_j are final, the corresponding value is initialized to True.
        Otherwise, such a value is initialized to False
        """
        
        for i in range(num_states):
            indistinguisable_states_i = []
            list_associated_states_i = []
            
            for j in range(i):
                list_associated_states_i_j = []
                
                if states_set[i] in final_states and states_set[j] in final_states:
                     indistinguisable_states_i.append(True)
                     
                elif states_set[i] not in final_states and states_set[j] not in final_states:
                     indistinguisable_states_i.append(True)
                     
                else:
                    indistinguisable_states_i.append(False)
                    
                list_associated_states_i.append(list_associated_states_i_j)

                
            indistinguisable_states.append(indistinguisable_states_i)
            lists_associated_states.append(list_associated_states_i)
        
        "Now, consider each pair of states that are not marked yet as distinguisable"
        
        for i in range(num_states):
            for j in range(i):
                if indistinguisable_states[i][j]:
                    for symbol in alphabet_symbols:
                        """ Look for the transitions of p_i and p_j """
                        transition_p_i_found = False
                        transition_p_j_found = False
                        k = 0
                    
                        while k < num_transitions and (not transition_p_i_found or not transition_p_j_found):
                            input_symbol = transitions[k].getInputSymbol()
                        
                            if input_symbol == symbol:
                                initial_state_transition = transitions[k].getInitialState()
                                final_states_transition = transitions[k].getFinalStates()
                        
                                if(initial_state_transition == states_set[i]):
                                    transition_p_i_found = True
                                    transition_pi =  final_states_transition[0]
                            
                                elif(initial_state_transition == states_set[j]):
                                    transition_p_j_found = True
                                    transition_pj =  final_states_transition[0]
                        
                            k+=1
                        
                        if not transition_pi == transition_pj:
                            """ Compute the indices of the transitions of p_i and p_j """
                            index_transition_pi = states_set.index(transition_pi)
                            index_transition_pj = states_set.index(transition_pj)
        
                            """ If the index of pi is lower than the index of, interchange both values """
                            if index_transition_pi < index_transition_pj:
                                aux = index_transition_pi
                                index_transition_pi = index_transition_pj
                                index_transition_pj = aux
        
                            """ If the states where p_i and p_j are transferred 
                            are not marked as distinguisable, then save (q_i and q_j)
                            as a pair associated to the pair of states of the transition.
                            If such states are marked as distinguisable, then mark q_i and q_j
                            as distinguisable. Do recursively the same with pairs in the list associated """
                            
                            
                            if indistinguisable_states[index_transition_pi][index_transition_pj]:
                                lists_associated_states[index_transition_pi][index_transition_pj].append((i,j))
                            
                    
                            else:
                                indistinguisable_states = self.__recursivelyMarkPairsStates(indistinguisable_states, i, j, lists_associated_states)
        
        """ Make the groups of indistinguisable states. For each state, check whether
        it belongs to some group by checking whether it is indistinguisable with 
        a previous state. If the state is already grouped, look for the 
        corresponding group and add the state to that group. Otherwise, 
        create a new group with only that state. """
        
        groups_indistingishable_states = []
        
        for i in range(num_states):
            state = states_set[i]
            state_grouped = False
            j = 0
            
            """Check whether there is a previous state indistinguisable with pi. 
            In the afirmative case, save the indistinguisable state"""
            while j < i and not state_grouped:
                if indistinguisable_states[i][j]:
                    state_grouped = True
                    indistinguisable_state_gruped = states_set[j]
            
                else:
                    j+=1
                    
            """If there is a previous state indistinguisable, look for the 
            group of that state and add the new state to such a group. """        
                    
            if state_grouped:
                group_found = False
                j = 0
                num_groups = len(groups_indistingishable_states)
                
                while j < num_groups and not group_found:
                    if indistinguisable_state_gruped in groups_indistingishable_states[j]:
                        group_found = True
                        groups_indistingishable_states[j].append(state)
                    
                    else:
                        j+=1


            else: # Create a new group with only the new state
                new_group = [state]
                groups_indistingishable_states.append(new_group)
            
        
        return groups_indistingishable_states
            
    """It computes the state associated with a group of states for the minimal automaton
    For example, if the group is {p_1,..,pn}, then the state is (p1,...,pn). """
    
    def __computeCorrespondingState(self, group_states):
        corresponding_state = group_states[0]
        num_states = len(group_states)
        
        for i in range(1,num_states):
            corresponding_state += "," + group_states[i]

        return corresponding_state          
                      
    """ It computes the minimal automaton. First, inaccessible states are removed.
    Then, gropus of indisguisable states are computed. Then, an automaton where
    the indistinghuisable states are grouped is computed""" 
    
        
    def minimalAutomaton(self):  
        alphabet_symbols = self.getAlphabetSymbols()
        deterministic_automaton = self.transformDeterministic()
        
        deterministic_automaton.deleteInaccessibleStates()
        
        final_states = deterministic_automaton.getFinalStates()
        initial_state = deterministic_automaton.getInitialState()
        transitions = deterministic_automaton.getTransitionFunction()
 
        groups_indistinguishable_states = deterministic_automaton.computeGroupsIndistinguishableStates()
        print("groups of indistinguisable states ")
        print(groups_indistinguishable_states)
        
        num_groups = len(groups_indistinguishable_states)
        
        states_minimal_automaton = []
        final_states_minimal_automaton = []
        
        """Go across the groups of states. For each group, consider the state of the minimal automaton. 
        If the initial state belongs the group, then the corresponding state 
        is the initial state of the minimal automaton. 
        If the states of the group are final, then the state is final in the minimal automaton"""
        
        
        for group_states in groups_indistinguishable_states:
            corresponding_state = self.__computeCorrespondingState(group_states)
                
            states_minimal_automaton.append(corresponding_state)  
            
             
            "Check whether the group corresponds to the initial state of the minimal automaton"
                        
            if initial_state in group_states: 
                initial_state_minimal_automaton = corresponding_state

                
            """ Check whether the group of states corresponds to a final state in the minimal automaton. """
             
            if group_states[0] in final_states:
                final_states_minimal_automaton.append(corresponding_state)    
        
        """ Compute the transition function. For each groups of states and symbol, check the transition
        of the first state of the group and find the corresponding group. """
        
        transitions_minimal_automaton = []
        
        for group_states in groups_indistinguishable_states:
            corresponding_state = self.__computeCorrespondingState(group_states)
        
            for symbol in alphabet_symbols:
                
                """ For the symbol and the state of the minimal automaton, look for the transition state. """
                
                transition_found = False
                j = 0
                num_transitions = len(transitions)
            
                while j < num_transitions and not transition_found:
                    initial_state_transition = transitions[j].getInitialState()
                    input_symbol = transitions[j].getInputSymbol()
                    
                    if initial_state_transition == group_states[0] and input_symbol == symbol:
                        transition_found = True
                        transition_state = transitions[j].getFinalStates()[0]
                        
                    else:
                        j = j+1
                              
    
                """Find the transition group, that is, the group to which the transition state belongs.
                Then, compute the state associated with the group and add the corresponding transition. """
                
        
                transition_group_found = False
                j = 0
                
                while j < num_groups and not transition_group_found:
                    if transition_state in groups_indistinguishable_states[j]:
                        transition_group_found = True
                        corresponding_transition_state = self.__computeCorrespondingState(groups_indistinguishable_states[j])
                        
                    else:
                        j = j+1
                        
                transition_minimal_automaton = Transition(corresponding_state,symbol,[corresponding_transition_state])
                transitions_minimal_automaton.append(transition_minimal_automaton)
        
        minimal_automaton = FiniteAutomaton(states_minimal_automaton, alphabet_symbols, transitions_minimal_automaton, initial_state_minimal_automaton, final_states_minimal_automaton)
        
        return minimal_automaton
    
    
    """It computes the automaton that accepts the inverse languaje. In order to build that automaton,
    it is essential that there is a unique final state. In such a case, the initial and final states 
    are changed and the transitions are reversed. """
    
    def computeReverseAutomaton(self):
        final_states = self.getFinalStates()
        initial_state = self.getInitialState()
        alphabet_symbols = self.getAlphabetSymbols()
        states_set = self.getStatesSet()
        
        if len(final_states) > 1:
            print("There must be a unique final state")
            return None  # FIX: explicit contract instead of relying on implicit fall-through
        
        else:
            #Change the initial and final states
            
            new_initial_state = final_states[0]
            new_set_final_states = [initial_state]
            
            "For each transition, create a new transition where the initial and final states are changed. "
        
            reverse_transitions = []
            
            transition_function = self.getTransitionFunction()
    
            for transition in transition_function:
                new_initial_state2 = transition.getFinalStates()[0]
                new_final_states = [transition.getInitialState()] 
            
                reverse_transition = Transition(new_initial_state2, transition.getInputSymbol(), new_final_states)
           
                reverse_transitions.append(reverse_transition)
    
            # FIX: use type(self) instead of the hardcoded FiniteAutomaton class, so
            # reversing a FiniteAutomatonNullable (an automaton with real epsilon
            # transitions) returns another FiniteAutomatonNullable. The reversed
            # transitions can still be epsilon-labeled (reversing a transition does
            # not remove its symbol), so returning the plain base class here silently
            # downgraded the result: its wordBelongs() no longer applied epsilon-
            # closure at all, giving wrong answers for words that legitimately relied
            # on an epsilon move (this is exactly what computeAssociatedAFNDLinearLeft
            # hits internally, since it reverses an automaton built with epsilon
            # transitions by construction).
            reverse_automaton = type(self)(states_set, alphabet_symbols, reverse_transitions, new_initial_state, new_set_final_states)
            
            return reverse_automaton
    
    def __str__(self):
        print("States set \n" )
        print (self.__states_set)
        print("\n")
        print("Input symbols \n")
        print(self.__alphabet_symbols)
        print("\n")
        print("Initial state \n")
        print(self.__initial_state)
        print("\n")
        print("Final states \n")
        print(self.__final_states)
        print("\n")

        
        for transition in self.__transition_function:
            print(transition)
            
        return ""
        