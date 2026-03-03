# -*- coding: utf-8 -*-
"""
Created on Wed Sep  4 16:21:54 2024

@author: Serafin
"""

from AFND import FiniteAutomaton
from AFND_nullable import FiniteAutomatonNullable
from automatonStack import AutomatonStack
from AutomatonStack_ICGrammar import automatonGrammar, grammarAutomatonStack
from grammar import GenerativeGrammar

path_file = "text/automaton_example.txt"
automaton = FiniteAutomaton.readAutomaton(path_file)
print(automaton)
path_transition_diagram = "transition_diagram"
automaton.showAutomaton(path_transition_diagram)
word = "011"
belonging = automaton.wordBelongs(word)
print("La palabra", word, "pertenece al lenguaje del autómata:", belonging)
deterministic = automaton.deterministicAutomaton()
print("El autómata es determinista:", deterministic)
# deterministic_automaton = automaton.transformDeterministic()
# deterministic_automaton.showAutomaton()
# complementary_automaton = automaton.complementaryAutomaton()
# print(complementary_automaton)
#path_file2 = "automaton_example2.txt"
#automaton2 = FiniteAutomaton.readAutomaton(path_file2)
#intersection_automaton = automaton.intersectionAutomaton(automaton2)
#intersection_automaton.showAutomaton()
#print(intersection_automaton)

#union_automaton = automaton.unionAutomaton(automaton2)
#union_automaton.showAutomaton()
#print(union_automaton)

#automaton.deleteInaccessibleStates()
#print(automaton)
#automaton.deleteErrorStates()
#print(automaton)

#minimal_automaton = automaton.minimalAutomaton()
#minimal_automaton.showAutomaton()

#path_nullable_automaton = "automaton_nullable2.txt"
#automaton_nullable = FiniteAutomatonNullable.readAutomaton(path_nullable_automaton)
#deterministic_automaton = automaton_nullable.transformDeterministic()
#deterministic_automaton.deleteInaccessibleStates()
#deterministic_automaton.showAutomaton()
#deterministic_automaton.deleteInaccessibleStates()
#print(deterministic_automaton)

#path_automaton_stack = "automaton_stack.txt"
#path_write_automaton_stack = "automaton_stack_written.txt"
#automaton_stack = AutomatonStack.readAutomaton(path_automaton_stack)
#automaton_stack.writeAutomaton(path_write_automaton_stack)
#word = "1001"
#belonging = automaton_stack.checkBelonging(word)
#print(belonging)

#deterministic = automaton_stack.isDeterministic()
#print(deterministic)

#path_automaton_stack2 = "automaton_stack2.txt"
#automaton_stack2 = AutomatonStack.readAutomaton(path_automaton_stack2)
#deterministic = automaton_stack2.isDeterministic()
#print(deterministic)

#word = "11c10"
#belonging = automaton_stack2.checkBelonging(word)
#print(belonging)

"""
path_automaton_final_states = "automaton_stack_final_states.txt"
automaton_final_states = automaton_stack.equivalentAutomatonFinalStates()
automaton_final_states.writeAutomaton(path_automaton_final_states)

path_automaton_stack3 = "automaton_stack3.txt"
automaton_stack3 = AutomatonStack.readAutomaton(path_automaton_stack3)
automaton_empty_stack = automaton_stack3.equivalentAutomatonEmptyStack()
path_automaton_empty_stack = "automaton_empty_stack.txt"
automaton_empty_stack.writeAutomaton(path_automaton_empty_stack)
"""

"""

path_grammar_automaton_stack = "grammar_to_automaton_stack.txt"
grammar_to_automaton_stack = GenerativeGrammar.readGrammar(path_grammar_automaton_stack)
automaton_from_grammar = automatonGrammar(grammar_to_automaton_stack)

path_write_automaton = "automaton_from_grammmar.txt"
automaton_from_grammar.writeAutomaton(path_write_automaton)

"""

"""
path_automaton_stack_to_grammar = "automaton_stack_to_grammar.txt"
automaton_stack_to_grammar = AutomatonStack.readAutomaton(path_automaton_stack_to_grammar)
grammar_from_automaton_stack = grammarAutomatonStack(automaton_stack_to_grammar)

path_write_grammar_from_automaton_stack = "grammar_from_automaton_stack.txt"
grammar_from_automaton_stack.writeGrammar(path_write_grammar_from_automaton_stack)
"""

"""
path_automaton_stack = "automaton_stack2.txt"
automaton_to_complementary = AutomatonStack.readAutomaton(path_automaton_stack)
complementary_automaton = automaton_to_complementary.complementaryDeterministic()
path_write_automaton_stack = "automaton_stack_complementary.txt"
complementary_automaton.writeAutomaton(path_write_automaton_stack)


path_automaton_stack = "automaton_stack.txt"
automaton_stack = AutomatonStack.readAutomaton(path_automaton_stack)
path_finite_automaton = "automaton_example.txt"
finite_automaton = FiniteAutomaton.readAutomaton(path_finite_automaton)
intersection_automaton = automaton_stack.intersectionFiniteAutomaton(finite_automaton)
path_write_intersection_automaton = "automaton_stack_intersection.txt"
intersection_automaton.writeAutomaton(path_write_intersection_automaton)



path1 = "grammar_operations1.txt"
path2 = "grammar_operations2.txt"

grammar_operations1 = GenerativeGrammar.readGrammar(path1)
#grammar_operations2 = GenerativeGrammar.readGrammar(path2)

path_operations1 = "grammar_operations1_written"
grammar_operations1.writeGrammar(path_operations1)

#grammar_union = grammar_operations1.unionGrammar(grammar_operations2)
"""

# path_grammar_belonging = "grammar_belonging.txt"
# grammar_belonging = GenerativeGrammar.readGrammar(path_grammar_belonging)
# grammar_belonging.transformChomsky()
# word = "baaba"
# grammar_belonging.checkBelongingCYK(word, True)


