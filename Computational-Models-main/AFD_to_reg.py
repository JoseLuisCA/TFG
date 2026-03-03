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
    
    elif expr_a[len(expr_a)-1]== "":  # If the last symbol of the expression a if the empty chain, then skip that symbol.    
        return "{}{}".format(expr_a[:-1], expr_b)
    
    elif expr_b[0]== "": # The same if the first symbol of the expression b is the empty chain
        return "{}{}".format(expr_a, expr_b[2:])
    
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
        return ""
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
                #r_ij_k = unionRegex(r_ij_k_1,concatenation)
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
           
    return regular_expression
