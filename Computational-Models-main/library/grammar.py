# -*- coding: utf-8 -*-
"""
General class for Generative grammar
"""

from typing import AbstractSet
from production_rule import ProductionRule
import networkx as nx
from Utils import getPowerset, extractSubsetFromLine, createStringList


variable_type = str  # type of the variables
terminal_type =  str # type of the terminal symbols

"""Class for context-free grammars """

class GenerativeGrammar: 
    __variable_symbols: AbstractSet[variable_type] # variables or non-terminal symbols
    __terminal_symbols: AbstractSet[terminal_type] # terminal symbols
    __production_rules: AbstractSet[ProductionRule] # production rules of the grammar
    __start_symbol: variable_type # Initial Symbol of the grammar
    
    """ The constructor of the class. It reads a grammar from a file, whose
    path is indicated in the argument file_name. """
    
    def __init__(self, variables, terminals, start, generative_rules) -> None:
         self.__variable_symbols = variables
         self.__start_symbol = start
         
         # self.validateInitialSymbol()
         
         self.__terminal_symbols = terminals
         
         #for rule in generative_rules:
          #   self.validateProductionRule(rule)
             
         self.__production_rules = generative_rules

        
    """ It validates the initial symbol by checking that  it 
    belongs to the variables list. """
    
    """
    
    def validateInitialSymbol(self) -> None:
        
        if start_symbol not in self.variable_symbols:
            # Error: initial symbol not valid
      
           """
    
    """ Get and Set methods"""
    
    def getVariableSymbols(self):
        return self.__variable_symbols
    
    def getInitialSymbol(self):
        return self.__start_symbol
    
    def getTerminalSymbols(self):
        return self.__terminal_symbols
    
    def getProductionRules(self):
        return self.__production_rules
    
    def setVariableSymbols(self, variables):
        self.__variable_symbols = variables
    
    def setInitialSymbol(self, start):
        self.__start_symbol = start
    
    def setTerminalSymbols(self, terminals):
        self.__terminal_symbols = terminals
    
    def setProductionRules(self, generative_rules):
        self.__production_rules = generative_rules
           
    """ Static method that creates a grammar from a list of strings
    The first string corresponds to the variables, the second one to the 
    terminal symbols, and the third string contains the production rules """
        
    @staticmethod
    def fromText(lines):
        variables = []
        terminals = []
        production_rules = []
        
        """ Obtain the list of variables and terminal symbols from the 
        lineas read, assuming that the first character of these lines is
        {, the last one is }, and that, in the lines, the elements are
        separated by commas """
        
        for line in lines:
            first_character = line[0]
                        
            """ For reading the variables or terminal symbols, skip until character '{' """
        
            if first_character == 'V':
                variables = extractSubsetFromLine(line, ',','{')
                start_variable = variables[0]
                
            elif first_character == 'T': 
                terminals = extractSubsetFromLine(line, ',','{')

                    
            elif first_character == '<' or first_character in variables: # Production line 
                production_parts = line.split("->")
                left_part = production_parts[0].strip() # The left part is before ->, removing blank spaces
                 
                """ We consider that in a line can be several rules with the same left part
                The right parts are separated by the character '|'"""
                
                string_right = production_parts[1].strip() # The left part is after ->, removing blank spaces
                string_right_parts = string_right.split("|")
                    
                for string_right_part in string_right_parts:
                     right_part = []
                     reading_variable = False
                     string_variable = ''
                      
                     """ Read the right part of a rule. It must be considered that
                     the variables are between <>. Hence, we must consider, in each moment,
                      whether we are reading '<', '>', or a character between these symbols """
            
                     for j in range(len(string_right_part)):
                        if reading_variable:
                            string_variable = string_variable + string_right_part[j]
                    
                            if string_right_part[j] == '>':
                                reading_variable = False
                                right_part.append(string_variable)
                
                        elif string_right_part[j] == '<':  
                            reading_variable = True
                            string_variable = '<'
                    
                        else:
                            right_part.append(string_right_part[j])
                    
              
                     rule = ProductionRule(left_part, right_part)
                     production_rules.append(rule)
        
            
        generated_grammar = GenerativeGrammar(variables, terminals,  start_variable, production_rules)
        
        return generated_grammar
    
    """
    Static method that creates a grammar given the path of a file.
    It reads the lines of the file and creates the grammar from such
    lines using the previous method.
    """
    @staticmethod
    def readGrammar(path_file):
        file = open(path_file)
        lines = file.readlines()
        generated_grammar = GenerativeGrammar.fromText(lines)
                
        return generated_grammar
    
    """
    It writes the grammar in a file given the name of the file
    """
    
    def writeGrammar(self, path_file):
        file = open(path_file, 'w')
        num_variables = len(self.__variable_symbols)
        num_terminals = len(self.__terminal_symbols)
        
        # Write the variables
        string_variables = createStringList("V", self.getVariableSymbols(), ",")
        file.write(string_variables + "\n")  
        
        # Write the terminal symbols
        
        string_terminals = createStringList("T", self.getTerminalSymbols(), ",")  
        
        file.write(string_terminals + "\n") 
        
        """A blank line before the production rules """
        file.write("\n")
        
        """ For each variable, consider all production rules in which
        that variable coincides with the left part.
        Separate all rules by | """
        
        for variable in self.__variable_symbols:
            string_rules = variable + " -> "
            appear_left_part = False
                
            for production_rule in self.__production_rules:
                left_part = production_rule.getLeftPart()
                right_part = production_rule.getRightPart()
                
                if left_part == variable:
                    
                    """ Add | before the right part if the variable has appeared in the 
                    left part of a previous production rule. """
                    
                    if appear_left_part:
                        string_rules = string_rules + "|"
                        
                    else:
                        appear_left_part = True
                    
                    for symbol in right_part: # Write each symbol in the right part           
                        string_rules = string_rules + symbol
                        
                    
        
            
            file.write(string_rules + "\n")
                
        file.close()
    
    """ It validates a production rule by checking that all symbols 
    in both parts of the rule are in the variables or terminal symbols
    lists and the left part contains at least one variable symbol. """
     
    def validateProductionRule(self, production_rule) -> None:
        variable_found = False
        left_part = production_rule.getLeftPart()
        right_part = production_rule.getRightPart()
        
                
       # if left_part not in self.variable_symbols:
            # error: the left part must be a variable symbol
            
        
     #   for symbol_rule in production_rule.right_part: # Go across all symbols of the left part
       #     if symbol_rule not in variable_symbols and symbol_rule not in terminal_symbols:
                # error: the symbol must be must be a variable or a terminal symbol

               
        
    """ It applies a production rule to a word. For this, the position 
    where the first part of the rule starts should be indicated. """
                
    def applyProductionRule(self, word, start_production, end_production, production_rule):
        if production_rule in self.__production_rules:
            left_part = production_rule.getLeftPart()
            right_part = production_rule.getRightPart()
            
            if word[start_production:end_production+1] == left_part:
                word_replaced = word[:start_production]+ "".join(right_part) + word[end_production+1:]
                                
                return word_replaced
            
    
    """ It checks whether the grammar is linear by the right. For each production rule,
    it checks that in the right part there is not a variable that
    is not in the last position. """
    
    
    def linearRight(self) -> bool:
       
        """ For each production rule, check that there is not a variable 
        before the last position """
        
        for production_rule in self.__production_rules:
            right_part = production_rule.getRightPart()
            num_symbols_right_part = len(right_part)
                  
            if num_symbols_right_part > 1:
                for i in range(num_symbols_right_part - 1):
                    if right_part[i] not in self.__terminal_symbols:
                        return False
                    
        return True
    
    """ It checks whether the grammar is linear by the left. Firstly, it checks
    whether the grammar is independent of context. Then, for each production rule,
    it checks that in the right part there not a variable that
    is not in the first position. """
    
    
    def linearLeft(self) -> bool:
      
        
        """ For each production rule, check that there is not a variable 
        after the first position """
        
        for production_rule in self.__production_rules:
            right_part = production_rule.getRightPart()
            num_symbols_right_part = len(right_part)
            
            if num_symbols_right_part > 1:
                for i in range(num_symbols_right_part - 1):
                    if right_part[i+1] not in self.__terminal_symbols:
                        return False
                    
        return True
    
    """It computes the grammar resulting from reverse the right part of the productions.
    Such a grammar generates the reverse languaje. """
    
    def computeReverseGrammar(self):
        reverse_productions = []
        
        "For each production, create a new production with the right part reversed"
        for production in self.__production_rules:
            left_part = production.getLeftPart()
            right_part = production.getRightPart()
            reversed_right_part = right_part[::-1]
            
            reverse_production = ProductionRule(left_part, reversed_right_part)
            reverse_productions.append(reverse_production)
            
        reverse_grammar = GenerativeGrammar(self.__variable_symbols, self.__terminal_symbols, self.__start_symbol, reverse_productions)
            
        return reverse_grammar
    
    """ Delete the productions of the grammar where a symbol (terminal or 
    non-terminal) appears. For each production, it firstly check whether 
    the symbol coincides with the left part. Then, it go across the symbols
    of the right part, checking whether they coincide. """
    
    def _deleteProductionsWithSymbol(self, symbol, verbose = False):
        i = 0
        
        while i < len(self.__production_rules):
            production_rule = self.__production_rules[i]
            left_part = production_rule.getLeftPart()
            
            if left_part == symbol:
                to_delete = True
                
            else:
                to_delete = False
                right_part = production_rule.getRightPart()
                j = 0
                num_symbols_right_part = len(right_part)
                
                while not to_delete and j < num_symbols_right_part:
                    
                    if right_part[j] == symbol:
                        to_delete = True
                    
                    else:
                        j = j+1
                        
            if to_delete:
                self.__production_rules.remove(production_rule)
                
                if verbose:
                    print("deleting the production " + production_rule)
                
            else:
                i = i+1
                
    """It determines the variables that can be replaced by terminal symbols Vt
     If the right part of the rule is composed of terminal symbols, then the variable 
    of the left part belongs to Vt. 
    If all variables in the right part are in Vt, then the variable 
    of the left part belongs to Vt """
    
    def determineVarablesReplacedbyTerminals(self):
        Vt = []
        production_rules = self.getProductionRules()
        
        """ For each production rule, if the variable of the left part
        is not in Vt yet, check whether all elements of the right part
        are terminal symbols """
        
        for production_rule in production_rules:
            left_part = production_rule.getLeftPart()
            right_part = production_rule.getRightPart()
            
            if left_part not in Vt:
                all_terminals = True;
                i = 0;
                num_symbols_right_part = len(right_part)
            
                while all_terminals and i < num_symbols_right_part:
                    if right_part[i] not in self.__terminal_symbols:
                        all_terminals = False;
                    
                    else:
                        i = i+1
                        
                if all_terminals:
                    Vt.append(left_part)
                    
        """ Include recursively all variables that can be eded in a terminal symbol 
        Recursive condition: If all elements of the right part are in Vt, then 
        the left part is in Vt""" 
        
                    
        list_changed = True
        
        while list_changed:
            list_changed = False
            
            for production_rule in production_rules:
                left_part = production_rule.getLeftPart()
                right_part = production_rule.getRightPart()
                
                if left_part not in Vt: 
                    all_replaced_by_terminal = True
                    i = 0;
                    num_symbols_right_part = len(right_part)
            
                    while all_replaced_by_terminal and i < num_symbols_right_part:
                        if right_part[i] not in self.__terminal_symbols and right_part[i] not in Vt:
                              all_replaced_by_terminal = False
                    
                        else:
                            i = i+1
                            
                    if all_replaced_by_terminal:
                        Vt.append(left_part)
                        list_changed = True
        
        return Vt
    
    """ It deletes the variables that cannot be replaced by a terminal symbol
    It determines Vt: variables that can be replaced by terminal symbols as follows:
    The variables not in Vt are removed, as well as the productions where 
    a variable not belonging to Vt.
    """
    
    def deleteVariablesNotReplacedByTerminals(self, verbose = False):
        Vt = self.determineVarablesReplacedbyTerminals()
        
        i = 0         
        while i < len(self.__variable_symbols):
            if self.__variable_symbols[i] not in Vt:
                
                if verbose:
                    print("Deleting the productions with symbol " + self.__variable_symbols[i])
                    
                self._deleteProductionsWithSymbol(self.__variable_symbols[i])
             
                if not self.__variable_symbols[i] == self.__start_symbol:
                    if verbose:
                        print("Deleting the symbol " + self.__variable_symbols[i])
                    
                    self.__variable_symbols.remove(self.__variable_symbols[i])
                    
                    
                else:
                    i = i+1
                    
            else:
                i = i+1
                      
    """ 
    It deletes the variables and terminal symbols that cannot be reached from the start symbol.
    It recursively searchs from the initial symbol. 
    """
    
    def deleteSymbolsNotReachable(self, verbose = False):
        start_symbol = self.getInitialSymbol()
        variables_reachable = [start_symbol] # the variables found as rechable
        variables_to_explore = [start_symbol] # the variables to explore
        terminal_symbols_reachable = [] # the terminal symbols found as rechable
        production_rules = self.getProductionRules()
        
        while len(variables_to_explore) >= 1: # while there are variables to explore
            """ Extract the first variable to explore """  
            variable_to_explore = variables_to_explore[0] 
            variables_to_explore.remove(variable_to_explore)
            
            """ Go across the productions with that variable in the left part """
            
            for production_rule in production_rules:
                left_part = production_rule.getLeftPart()
                right_part = production_rule.getRightPart()

                if left_part == variable_to_explore:
                    """Go across the symbols of the right part.
                    If the symbol is a variable and is not included in the variables reachable
                    include it in the variables reachable and to analyze
                    If the symbol is terminal and is not included in the 
                    terminal symbols reachable include it """
                    for symbol in right_part:
                        if symbol in self.__variable_symbols and symbol not in variables_reachable:
                            variables_reachable.append(symbol)
                            variables_to_explore.append(symbol)
                            
                        elif symbol in self.__terminal_symbols and symbol not in terminal_symbols_reachable:
                            terminal_symbols_reachable.append(symbol)
                
        """ Delete the variables and terminal symbols that are not reachable from the
        initial symbol, as well as the productions where they appear """
        
        i = 0
        
        while i < len(self.__variable_symbols):
            variable = self.__variable_symbols[i]
                
            if variable not in variables_reachable:
                
                if verbose:
                    print("Deleting the productions with the variable " + variable)
                    print("Deleting the variable " + variable)
                    
                self._deleteProductionsWithSymbol(variable)
                self.__variable_symbols.remove(variable)
                     
            else:
                i = i+1
                    
        i = 0
        
        while i < len(self.__terminal_symbols):
            symbol = self.__terminal_symbols[i]
                
            if symbol not in terminal_symbols_reachable:
            
                if verbose:
                    print("Deleting the terminal symbol " + symbol)
                    
                self._deleteProductionsWithSymbol(symbol)
                self.__terminal_symbols.remove(symbol)
                    
                     
            else:
                i = i+1
                     
            
    """It deletes the useless symbols and productions of the grammar. 
    First step: Delete the variables from which no terminal symbol can be reached
    Second step: Delete the variables and terminal symbols 
   that are not reachable from the initial symbol. The productions where
   these symbols appear are also removed. """
    
    
    def deleteUselessSymbolsProductions(self, verbose = False):
        if verbose:
            print("Deleting the variables that cannot be replaced by terminal symbols")
            
        self.deleteVariablesNotReplacedByTerminals(verbose)
        
        if verbose:
            print("Deleting the variables and symbols not reachable from the initial symbol")
        
        self.deleteSymbolsNotReachable(verbose)
    
    
    """ It computes the set of nullable variables. 
    Basic condition: if a variable is in the left 
    of a null production, then it is nullable.
    Recursive condition: If all variables in the 
    right part of a production are nullable, then 
    the variable of the left part is nullable
    """
    
    def computeNullableVariables(self):
        nullable_variables = []
        production_rules = self.getProductionRules()  
        
        """If A -> \epsion, then A is nullable"""
        for production_rule in self.__production_rules: 
            left_part = production_rule.getLeftPart()
            right_part = production_rule.getRightPart()
            
            if left_part not in nullable_variables and len(right_part) == 0:
                nullable_variables.append(left_part)
            
        """While there are changes in the list of nullable variables,
        Go across the productions for which the left part is not in the list
        If the all symbols in the left part are nullable, then the 
        variable of the left part is also nullable. """ 
        
        list_changed = True
        
        while list_changed:
            list_changed = False
            
            for production_rule in production_rules: 
                left_part = production_rule.getLeftPart()
                right_part = production_rule.getRightPart()
                
                if left_part not in nullable_variables:
                    #Search for a non-nullable symbol in the right part
                    all_nullable = True
                    num_symbols_right_part = len(right_part)
                    i = 0
                    
                    while all_nullable and i < num_symbols_right_part:
                        if right_part[i] not in nullable_variables:
                            all_nullable = False
                            
                        else:
                            i = i+1
        
                    if all_nullable:
                        nullable_variables.append(left_part)
                        list_changed = True
                        
        return nullable_variables
    
        
    """ It eliminates the null productions of the grammar: Firstly, 
    the set of variables that can generate the empty work is computed. 
    Then, the null productions are deleted, adding the productions that
    compensate the elimination. """
    
    def deleteNullProductions(self, verbose = False):
        nullable_variables = self.computeNullableVariables()
        
        if verbose: 
            print("List of nullable variables ")
            print(nullable_variables)

        i = 0
        
        # Delete the null productions
        while i < len(self.__production_rules):
            production_rule = self.__production_rules[i]
            right_part = production_rule.getRightPart()
            
            if len(right_part) == 0:
                 self.__production_rules.remove(production_rule)
                 
                 if verbose:
                     print("Removing the production ")
                     print(production_rule)
                 
            else:
                i = i+1
        
        rules_to_add = [] # The rules to add for compensating the elimination of the null productions
                
        for production_rule in self.__production_rules:
           left_part = production_rule.getLeftPart()
           right_part = production_rule.getRightPart()
            
           """Compute the list of the nullable symbols in the right part"""
           
           nullable_symbols_right_part = []
            
           for symbol in right_part:
                if symbol in nullable_variables:
                    nullable_symbols_right_part.append(symbol)
                    
             
           # Extract the subsets of nullable symbols     
           subsets_nullable = getPowerset(nullable_symbols_right_part)
                
           """For each subset of nullable symbols that is not the total one,
           Add a new production rule with the same left part and the nullable
           symbols that are not in set subset, whenever the new production is 
           not null (has at least one symbol in the right part)"""
           for subset_nullable in subsets_nullable:
               if len(subset_nullable) > 0:
                   symbols_new_right_part = []
                   
                   for symbol in right_part:
                       if symbol not in nullable_symbols_right_part or symbol not in subset_nullable:
                            symbols_new_right_part.append(symbol)
                   
                   if len(symbols_new_right_part) > 0: # Check that the new production is not null
                       new_production_rule = ProductionRule(left_part, symbols_new_right_part)
                       rules_to_add.append(new_production_rule)
                         
                       if verbose:
                           print("Adding the production ")
                           print(new_production_rule)
           
        
           """ Add the rules that are not in the rules of the grammar """
            
        for rule in rules_to_add:
            if rule not in self.__production_rules:
                self.__production_rules.append(rule)
       
    """It computes H = the set of pairs (A,B) such that B is derivable from A 
        Basic condition: if A-> B, then (A,B) belongs to H
        Recursive condition:If (A,B) (B,C) belong to H, then 
        (A,C) belongs to H"""
        
    def computeSetDerivablePairs(self):
        set_derivable_pairs = []
        variable_symbols = self.getVariableSymbols()
        production_rules = self.getProductionRules()
        
        """Insert the pairs (A,B) for which there is a production A -> B """
        
        for production_rule in production_rules:
            right_part = production_rule.getRightPart()
            
            if len (right_part) == 1 and right_part[0] in variable_symbols:
                left_part = production_rule.getLeftPart()
                new_tuple = (left_part, right_part[0])
                set_derivable_pairs.append(new_tuple)
                
        list_changed = True
        
        """ Search for the pairs of tuples (A,B), (B, C) in H 
        to insert (A, C) in H if there is not in the list yet
        Continue while the list is changed """
        
        while list_changed:
            list_changed = False
            num_pairs = len(set_derivable_pairs)
            
            for i in range(0,num_pairs-1):
                for j in range(i+1, num_pairs):
                    if set_derivable_pairs[i][1] == set_derivable_pairs[j][0]:
                        new_tuple = (set_derivable_pairs[i][0], set_derivable_pairs[j][1])
                        
                        if new_tuple not in set_derivable_pairs:
                            set_derivable_pairs.append(new_tuple)
                            list_changed = True
                
        
        return set_derivable_pairs
        
    """ It eliminates the unitary productions of the grammar: firstly, 
    the pairs of variables such that one of them is computed from the other 
    Then, the unitary productions are deleted, adding the productions that
    compensate the elimination. """
    
    def deleteUnitaryProductions(self, verbose = False):
        set_derivable_pairs = self.computeSetDerivablePairs()
        
        if verbose:
            print("List of derivable pairs ")
            print(set_derivable_pairs)
            
        # delete the unitary productions
        i = 0
        
        while i < len(self.__production_rules):
            production_rule = self.__production_rules[i]
            right_part = production_rule.getRightPart()
            
            
            if len (right_part) == 1 and right_part[0] in self.__variable_symbols:
                self.__production_rules.remove(production_rule)
                
                if verbose:
                    print("Deleting the production ")
                    print(production_rule)
                
            else:
                i = i+1
                
        """ For each tuple (A,B) in the set of derivable pairs, 
        for each production B->alpha, add a production A -> alpha """
        
        for pair in set_derivable_pairs:
            for production_rule in self.__production_rules:
                left_part = production_rule.getLeftPart()
                right_part = production_rule.getRightPart()
                
                if left_part == pair[1]:
                    new_production_rule = ProductionRule(pair[0], right_part)
                    
                    if new_production_rule not in self.__production_rules:
                        self.__production_rules.append(new_production_rule)
                        
                        if verbose:
                           print("Adding the production ")
                           print(new_production_rule)
        
        
    """ It tranforms the grammar into the normal Chomsky form. 
    Firstly, for each production with two or more symbols in the right
    part, add a variable per terminal symbol that appears. In that 
    production, the terminal symbol is replaced by the new variable.
    Secondly, for each production with m variables, wth m >= 3, m-2 
    variables are added, and the production is replaced by a set of 
    productions of length 2
    """
    
    def transformChomsky(self, verbose = False):
       self.deleteNullProductions(verbose)
       self.deleteUnitaryProductions(verbose)
               
       for production_rule in self.__production_rules:
          right_part = production_rule.getRightPart() 
           
          num_symbols_right_part = len(right_part)
          
          if num_symbols_right_part > 1: # Go accross the non-unitary productions
               
               for i in range(num_symbols_right_part):
                   symbol = right_part[i]
                   
                   if symbol in self.__terminal_symbols: # Go across the terminal symbols of the right part of the production
                      variable_to_add = "<C" + symbol + ">" # Add a variable preceded by C
                       
                      """Add a production of the form Ca -> a, if not added """
                      if variable_to_add not in self.__variable_symbols: 
                           self.__variable_symbols.append(variable_to_add)
                           
                           if verbose:
                               print("Adding the variable " + variable_to_add)
                           
                           new_production_rule = ProductionRule(variable_to_add, [symbol])
                           self.__production_rules.append(new_production_rule)
                           
                           if verbose:
                               print("Adding the production ")
                               print(new_production_rule)
                        
                      """Replace a with Ca in the production"""
                      production_rule.getRightPart()[i] = variable_to_add
            
       i = 0
       counter_new_variables = 1 # counter for the variables Di to add
         
       for i in range(len(self.__production_rules)):
          production_rule = self.__production_rules[i]
          left_part = production_rule.getLeftPart()
          right_part = production_rule.getRightPart()
          num_symbols_right_part = len(right_part)
          
          if num_symbols_right_part > 2: # For each production A-> B1...Bm with m>=3
              
              " Add the productions of the form A -> B1D1, D1 -> B2D2,,... Dm-2->Bm-1Bm "
        
              previous_variable = left_part
        
              for j in range(num_symbols_right_part - 2):
                  new_variable = "<D" + str(counter_new_variables) + ">"
                  self.__variable_symbols.append(new_variable)
                  
                  if verbose:
                      print("Adding the variable " + new_variable)
                  
                  counter_new_variables = counter_new_variables + 1
                  new_right_part = [right_part[j], new_variable]
                  new_production = ProductionRule(previous_variable, new_right_part)
                  self.__production_rules.append(new_production)
                  previous_variable = new_variable
                  
                  if verbose:
                      print("Adding the production ")
                      print(new_production)

              """ Add the last production rule Dm-2->Bm-1Bm """
              new_right_part = [right_part[num_symbols_right_part - 2], right_part[num_symbols_right_part - 1]]
              new_production = ProductionRule(previous_variable, new_right_part)
              self.__production_rules.append(new_production)
             
              if verbose:
                 print("Adding the production ")
                 print(new_production)
              
              self.__production_rules.remove(production_rule) # Delete A -> B1....Bm

              if verbose:
                  print("Removing the production ")
                  print(production_rule)

          else:
              i = i+1
    
    """It checks whether the conditions for transform the grammar in the 
    Greibach Normal Form are satisfied. Such conditions are:
    If a production has a unique symbol in the right part, such a symbol is terminal
    All symbols from the second one are variables (non-terminal)"""
              
    def greibachAppliable(self, verbose = False):
        conditions_satisfied = True
        i = 0
        terminal_symbols = self.getTerminalSymbols()
        variable_symbols = self.getVariableSymbols()
        production_rules = self.getProductionRules()
        num_production_rules = len(production_rules)
        
        while conditions_satisfied and i < num_production_rules:
            production_rule = production_rules[i]
            right_part = production_rule.getRightPart()
            num_symbols_right_part = len(right_part)
            
            # If there is a unique symbol, then it must be terminal
            if num_symbols_right_part == 1 and right_part[0] not in terminal_symbols:
                conditions_satisfied = False
                
                if verbose:
                    print("Greibach cannot be applied due to the production ")
                    print(production_rule)
            
            #If the production is not non-unitary, then all symbols from the second one must be variables
            else:
                j = 1
                non_terminal_found = False
                
                while not non_terminal_found and j < num_symbols_right_part:
                   if right_part[j] not in variable_symbols: 
                        non_terminal_found = True  
                    
                   else:
                       j = j+1
                    
            
                if non_terminal_found:
                    conditions_satisfied = False
                    
                    if verbose:
                        print("Greibach cannot be applied due to the production ")
                        print(production_rule)
                    
            i = i+1
        
        return conditions_satisfied
        
    """ First deletion operation of the Greibach algorithm
    Delete the production A-> B alpha. For each B -> beta
    Include A -> betaalpha
    """
    
    def firstDeletionGreibach(self, production_to_delete, verbose = False):
        self.__production_rules.remove(production_to_delete)
        
        if verbose:
           print("Deleting the production ")
           print(production_to_delete)
        
        first_variable_right = production_to_delete.getRightPart()[0]
        remaining_right_part = production_to_delete.getRightPart()[1:]
        
        for production_rule in self.__production_rules:
            left_part = production_rule.getLeftPart()
            
            if left_part == first_variable_right:
                right_part = production_rule.getRightPart()
                new_right_part = right_part + remaining_right_part
                new_production_rule = ProductionRule(production_to_delete.getLeftPart(), new_right_part)
                
                if new_production_rule not in self.__production_rules:
                    self.__production_rules.append(new_production_rule)
                    
                    if verbose:
                        print("Adding the production ")
                        print(new_production_rule)
        
    """Second deletion operation of the Greibach algorithm. Given a 
    variable A, delete all productions of the form A-> A alpha
    Delete the production A-> B alpha. For each B -> beta
    Include A -> betaalpa
    """
    
    def secondDeletionGreibach(self, variable, verbose = False):
        string_new_variable = "<B" + variable + ">"
        rules_to_add = []
        
        # Add a new variable B_A.
        if string_new_variable not in self.__variable_symbols:
            self.__variable_symbols.append(string_new_variable)
            
            if verbose:
                print("Adding the variable " + string_new_variable)
        
        i = 0
        while i < len(self.__production_rules):
            production_rule = self.__production_rules[i]
            left_part = production_rule.getLeftPart()
            right_part = production_rule.getRightPart()
            
            if left_part == variable: # If the production is of the form A -> A\alpha

                if right_part[0] == variable:

                    remaining_right_part = right_part[1:] # Extract \alpha
                    # Add B_A -> alpha
                    new_rule1 = ProductionRule(string_new_variable, remaining_right_part)
                     # Add B_A -> alphaB_A
                    new_right_part = remaining_right_part + [string_new_variable]
                    new_rule2 = ProductionRule(string_new_variable, new_right_part)
                
                    if new_rule1 not in self.__production_rules:
                        rules_to_add.append(new_rule1)
                        
                        if verbose:
                           print("Adding the production " + new_rule1)
                           print(new_rule1)
                           
                    if new_rule2 not in self.__production_rules:
                        rules_to_add.append(new_rule2)
                        
                        if verbose:
                           print("Adding the production ")
                           print(new_rule2)
                        
                    self.__production_rules.remove(production_rule)
                    
                    if verbose:
                           print("Removing the production ")
                           print(production_rule)

                # If the production is A -> \betha, and \betha
                #  does not start by A, then add the rule A -> \bethaB_A 
                
                else: 
                    new_right_part = right_part + [string_new_variable]
                    new_rule = ProductionRule(left_part, new_right_part)
                    
                    if new_rule not in self.__production_rules:
                        rules_to_add.append(new_rule)
                        
                        if verbose:
                           print("Adding the production ")
                           print(new_rule)
                        
                    i = i+1

            else:
                i = i+1
                
            
        for new_rule in rules_to_add:
            self.__production_rules.append(new_rule)
            
            if verbose:
                print("Adding the production ")
                print(new_rule)
    
    """First part of the Greibach algorithm. It aims that all productions have the form
    A -> a\alpha, A_i -> A_j\alpha, B_j -> Ai\alpha, where Bk is the variable that is
    added when Ak is deleted with the second operation. """
    
    def first_part_Greibach(self, verbose = True):
        num_variables = len(self.__variable_symbols)
        num_production_rules = len(self.__production_rules)
        
        for i in range(num_variables): # for each i = 1...m
            for j in range(i): #f for each j = 1,,,i-1
                k = 0
                while k < num_production_rules:
                    production_rule = self.__production_rules[k]
                    left_part = production_rule.getLeftPart()
                    right_part = production_rule.getRightPart()
                    """For each production of the form Ai -> Aj\alpha
                    Delete  Ai -> Aj\alpha with the first deletion """
                    if left_part == self.__variable_symbols[i] and right_part[0] == self.__variable_symbols[j]:
                        self.firstDeletionGreibach(production_rule)
                        
                        if verbose:
                            print("Making the first deletion of the Greibach algorithm with the production ")
                            print(production_rule)
        
                    else:
                        k = k+1
        
            """ If there is a production of the form Ai -> Ai\alpha
             Delete Ai with the second operation """
            k = 0
            while k < num_production_rules:
                production_rule = self.__production_rules[k]
                left_part = production_rule.getLeftPart()
                right_part = production_rule.getRightPart()
                
                if left_part == self.__variable_symbols[i] and right_part[0] == self.__variable_symbols[i]:
                   self.secondDeletionGreibach(self.__variable_symbols[i])
                  
                   if verbose:
                       print("Making the second deletion of the Greibach algorithm with the variable " + self.__variable_symbols[i])
                    
                else:
                    k = k+1
    """Second and last part of the Greibach algorithm """
    
    def second_part_Greibach(self, verbose = True):
        num_variables = len(self.__variable_symbols)
        num_production_rules = len(self.__production_rules)
        
        """For each i = m-1...1. For each production of the form A_i -> A_j\alpha, j > i,
        Delete A_i -> A_j\alpha with the first operation """
        for i in reversed(range(num_variables - 1)):
            for j in range(i+1, num_variables):
                k = 0
                while k < num_production_rules:
                    production_rule = self.__production_rules[k]
                    left_part = production_rule.getLeftPart()
                    right_part = production_rule.getRightPart()
                    
                    if left_part == self.__variable_symbols[i] and right_part[0] == self.__variable_symbols[j]:
                        self.firstDeletionGreibach(production_rule)
                           
                        if verbose:
                            print("Making the first deletion of the Greibach algorithm with the production ")
                            print(production_rule)
                    
                    else:
                        k = k+1
        """ For each i = 1,2...m. For each production B_j -> A_i\alpha
        Delete  B_j -> A_i\alpha with the first operation """
         
        for i in range(num_variables):
            for j in range(num_variables):
                string_added = "<B" + self.__variable_symbols[j] + ">"
                k = 0
                while k < num_production_rules:
                    production_rule = self.__production_rules[k]
                    left_part = production_rule.getLeftPart()
                    right_part = production_rule.getRightPart()
            
                    if left_part == string_added and right_part[0] == self.__variable_symbols[i]:
                        self.firstDeletionGreibach(production_rule)
                        
                        if verbose:
                            print("Making the first deletion of the Greibach algorithm with the production")
                            print(production_rule)

                    else:
                        k = k+1
                        
                    

    """It transform the grammar into the Greibach normal form via the two parts described above """
    
    def transformGreibach(self, verbose = False):
        
        if verbose:
            print("Running the first part of the Greibach algorithm")
        
        self.first_part_Greibach(verbose)
        
        if verbose:
            print("Running the second part of the Greibach algorithm")
        
        self.second_part_Greibach(verbose)
    """ Recursive method that belongs whether a word can be generated by a grammar in Greibach normal form
    Remaining word is the part of the word that must be generated and current word is the word that has not 
    been derived yet (the non-terminal symbols of the word derived)
    """

    def checkBelongingRecursiveGreibach(self, remaining_word, current_word, verbose = False):
        """Base case: If there is no more word to generate, the word belongs if, and only if,
        there is no more part of the word to derive"""
        
        if len(remaining_word) == 0:
            
            if verbose:
                print("Remaining word to generate " + current_word)
            
            belongs = len(current_word) == 0
            return belongs
    
        
        else:
            
            """ If there is more word to be generated, look for for each production rule such that the 
                first symbol of the right part coincides with the first symbol of the word to generate and 
                make a recursive call to the method with the remaining parts of the word to derive and the
                word to be generated (removing the first symbol). 
                If the word can be generated witn some of these rules, the method returns True. Otherwise,
                the method returns false"""
            
            
            for production_rule in self.__production_rules:
                left_part = production_rule.getLeftPart()
                right_part = production_rule.getRightPart()
                
                if right_part[0] == remaining_word[0]:
                    num_symbols_left_part = len(left_part)
                    i = 0
                    discrepance = False
                    
                    while i < num_symbols_left_part and not discrepance:
                        if not left_part[i] == current_word[i]:
                            discrepance = True
                                 
                        else:
                            i = i+1
                            
                    if not discrepance:
                    
                        word_derived = self.applyProductionRule(current_word, 0,num_symbols_left_part-1, production_rule)
                        partial_belonging = self.checkBelongingRecursiveGreibach(remaining_word[1:],word_derived[1:])
                    
                        if partial_belonging:
                            return True
            
            
            return False

    def wordBelongsGreibach(self, word, verbose = False):
        self.transformGreibach(verbose)
        belongs = self.checkBelongingRecursiveGreibach(word, self.__start_symbol, verbose)
        return belongs
    
    """Check whether two grammars have the same terminal symbols"""
    
    def coincideTerminalSymbols(self, second_grammar):
        terminal_symbols = self.getTerminalSymbols()
        
        """ Check that both list have the same lenght and that each symbol
        of the first list is in the second one. """
        
        if len(terminal_symbols) == len(second_grammar.getTerminalSymbols()):
            coincide_terminal_symbols = True
            
            i = 0
            
            while coincide_terminal_symbols and i < len(terminal_symbols):
                if terminal_symbols[i] in second_grammar.getTerminalSymbols():
                    i = i+1
                    
                else:
                    coincide_terminal_symbols = False

            
        else:
            coincide_terminal_symbols = False
            
        return coincide_terminal_symbols
        
    """ It makes the union of the grammar with another grammar
    The new grammar has the productions S -> S_1, S -> S_2, and the 
    productions of both grammars """
    
    def unionGrammar(self, second_grammar):
        
        coincide_terminal_symbols = self.coincideTerminalSymbols(second_grammar)
            
        if  coincide_terminal_symbols: # It is necessary that both grammars have the same terminal symbols
            start_variable_union = "<S_u>"
            variables_union = [start_variable_union]
            
            """Include the variables of both grammar in the variables of the union grammar
            Remark that the variable of a grammar can not be included in the variables
            of the other grammar. If this is not satisfies, raise error. """
            
            for variable in self.__variable_symbols:
                if variable not in second_grammar.getVariableSymbols():
                    variables_union.append(variable)
                    
            for variable in second_grammar.getVariableSymbols():
                if variable not in self.__variable_symbols:
                    variables_union.append(variable)
                    
            # Add the production rules. The first rules are S -> S_1, S-> S_2
            
            first_rule = ProductionRule(start_variable_union, [self.__start_symbol])
            second_rule = ProductionRule(start_variable_union, [second_grammar.getInitialSymbol()])

            # Add the productions of both grammars

            production_rules_union = [first_rule, second_rule] + self.__production_rules + second_grammar.getProductionRules()
                 
            
            union_grammar = GenerativeGrammar(variables_union, self.__terminal_symbols,  start_variable_union, production_rules_union)
        
            return union_grammar
        
        
    """ It makes the concatenation of the grammar with another grammar
    The new grammar has the production S -> S_1S_2, and the productions of both grammars """
    
    def concatenationGrammar(self, second_grammar):
        
        coincide_terminal_symbols = self.coincideTerminalSymbols(second_grammar)
            
        if  coincide_terminal_symbols: # It is necessary that both grammars have the same terminal symbols
            start_variable_concatenation = "<S_c>"
            variables_concatenation = [start_variable_concatenation]
            
            """Include the variables of both grammar in the variables of the union grammar
            Remark that the variable of a grammar can not be included in the variables
            of the other grammar. If this is not satisfies, raise error. """
            
            for variable in self.__variable_symbols:
                if variable not in second_grammar.getVariableSymbols():
                    variables_concatenation.append(variable)
                    
            for variable in second_grammar.getVariableSymbols():
                if variable not in self.__variable_symbols:
                    variables_concatenation.append(variable)
                    
            # Add the production rules. The first rules are S -> S_1, S-> S_2
            
            first_rule = ProductionRule(start_variable_concatenation, [self.__start_symbol, second_grammar.getInitialSymbol()])


            # Add the productions of both grammars

            production_rules_concatenation = [first_rule] + self.__production_rules + second_grammar.getProductionRules()
            
            concatenation_grammar = GenerativeGrammar(variables_concatenation, self.__terminal_symbols,  start_variable_concatenation, production_rules_concatenation)
        
            return concatenation_grammar
    
    
    """ It makes the clausure of a grammar. The new grammar has the productions S_v->SS_v,   S_v -> \epsilon
    and the productions of the other grammar """   
    
    def clausureGrammar(self):
        start_variable_clausure = "<S_v>"
        variables_clausure = [start_variable_clausure] + self.__variable_symbols
        
        first_rule = ProductionRule(start_variable_clausure, [self.__start_symbol, start_variable_clausure]) # S_v->SS_v
        second_rule = ProductionRule(start_variable_clausure, []) # S_v-> \epsilon

        production_rules_clausure = [first_rule, second_rule] + self.__production_rules
        
        clausure_grammar = GenerativeGrammar(variables_clausure, self.__terminal_symbols,  start_variable_clausure, production_rules_clausure)
        
        return clausure_grammar
    
        
    """ It checks whether the language generated by the grammar is empty
    It can be done by checking whether the initial symbols can be replaced 
    by terminal symbols (first part of the algorithm that deletes useless 
    symbols and productions. """

    def emptyLanguaje(self):
        variables_replaced_by_terminals = self.determineVarablesReplacedbyTerminals()
        empty_languaje = self.__start_symbol not in variables_replaced_by_terminals
        
        return empty_languaje
        
    """
    It checks wether the languaje generated by a grammar is infinity
    A directed graph is built, in which the nodes are the variables and 
    there is an arc A - > B if, and only if, there is a production of the 
    form A -> alphaBbeta.
    The languaje in infinity if, and only if, this graph has some cycle
    """
    
    def infinityLanguaje(self):
        
        """ Delete useless symbols and productions, 
        as well as null and unitary productions"""
        
        self.deleteUselessSymbolsProductions()
        self.deleteNullProductions()
        self.deleteUnitaryProductions()
        
        graph = nx.DiGraph()
        
        graph.add_nodes_from(self.__variable_symbols) # copy the variables in the nodes
        
        """ For each production rule A->\alpha: 
            For each variable in \alpha B: If there is no an arc A->B,
            add the arc A -> B
        """
        
        for production_rule in self.__production_rules:
            left_part = production_rule.getLeftPart()
            right_part = production_rule.getRightPart()
            
            for symbol_right in right_part:
                if symbol_right in self.__variable_symbols:
                    graph.add_edge(left_part, symbol_right)
                    
      
        # The languaje in infinity if, and only if, there is at least one cycle
        cycles = nx.recursive_simple_cycles(graph)
        infinity = len(cycles) > 0
        
        return infinity
    
    """It checks whether a word u belongs to the grammar
    via the CYK algorithm
    u_i,j = subchain that starts in the position i and has length j
    Determine Vij = variables that generate u_i,j
    """
    
    def checkBelongingCYK(self, word, verbose = False):
        start_symbol = self.getInitialSymbol()
        variables_generate_subchain = []
        
        """ Determine V_i1 = {A | A->a is a production} and the i-th
        symbol of u is a"""
               
        variables_generate_symbols = []
        
        for i in range(len(word)):
            
            if verbose:
                print("Determining V_" + str(i) + "1")
            
            V_i1 = []
            
            for production_rule in self.__production_rules:
                right_part = production_rule.getRightPart()
                
                if right_part[0] == word[i]:  # If there production is unitary and the i-th symbol in in the right
                   left_part = production_rule.getLeftPart()
                   V_i1.append(left_part) 
                   
                   if verbose:
                       print("Adding " + left_part + " to V_" + str(i) + "1")
            
        
            variables_generate_symbols.append(V_i1)
            
        variables_generate_subchain.append(variables_generate_symbols)
        
        """ Recursive condition: If A->BC is a production and B \in V_ik and V \in V_i+k,jk,
        then A \in V_ij """
        
        for j in range(2,len(word)+1): # Go across all possible length of the word, starting from 2
            variables_generate_lengthj = []
            
            for i in range(len(word) - j + 1): # Go across all possible start positions of the word, given the length
                V_ij = []
                
                if verbose:
                    print("Determining V_" + str(i) + str(j))
                
                for k in range(j-1): # Go across the cut points
                    for production_rule in self.__production_rules:
                        right_part = production_rule.getRightPart()
                        
                        """  Go across the non-unitary productions A->BC
                            Check whether B \in V_ik and C \in V_i+k,j-k """
                        if len(right_part) == 2: 
                            if right_part[0] in variables_generate_subchain[k][i] and right_part[1] in variables_generate_subchain[j-k-2][i+k+1]:
                                left_part = production_rule.getLeftPart()
                                if left_part not in V_ij:
                                    V_ij.append(left_part)
                                    
                                    if verbose:
                                        print("Adding " + left_part + " to V_" + str(i) + str(j))
                                    
                                    
                variables_generate_lengthj.append(V_ij)
                
            variables_generate_subchain.append(variables_generate_lengthj)
            
        """ The word can be generated if, and only if, the start symbol 
        belongs to V_1n"""
                
        belongs = start_symbol in variables_generate_subchain[len(word) -1][0]
        
        return belongs
    
    """
    It checks whether a word u can be generated by a grammar via the Early algorithm
    u[i..j] = subchain of u from position i to position j
    Registers (i,j,A,\alpha,\betha) A-> \alpha\betha production of the grammar
    u[i+1....j] derivabke from \alpha. 
    Aim: find the k such that \beta derives to u[j+1...k]. In such a case,
    A derives to u[i+1...k].
    For all j, REGISTERS[j] contains all registers of the form Registers (i,j,A,\alpha,\betha)
    """
    
    def checkBelongingEarly(self, word, verbose = False):
        start_symbol = self.getInitialSymbol()
        production_rules = self.getProductionRules()
        length_word = len(word)
        """Step 1. Initiaization: REGISTERS [0] = {(0,0,S,\epsilon,\betha): S -> \betha is a production}
        j = 0"""
        
        first_registers = []
        
        if verbose:
            print("Determining REGISTERS [0] ")
        
        for production_rule in production_rules:
            left_part = production_rule.getLeftPart()
            right_part = production_rule.getRightPart()
            
            if left_part == start_symbol:
                register = (0,0,start_symbol, "", right_part)
                first_registers.append(register)
                
                if verbose:
                    print("Adding ")
                    print(register)
                
        total_registers = [first_registers]
        j = 0
        
        while j < length_word:
            """Step 2. Clausure: For all register (i,j,A,\alpha,\betha|gamma) in REGISTERS[j]:
            For each production B -> deltha: create the register (j,j,B,\epsilon,\deltha)
            e insert it in REGISTERS[j]. Repeat recursively for all registers inserted. """
            
            if verbose:
                print("Clausure")
            
            for register in total_registers[j]:
                for production_rule in production_rules:
                    left_part = production_rule.getLeftPart()
                    right_part = production_rule.getRightPart()
                    
                    if len(register[4]) > 0:
                        if left_part == register[4][0]:
                            new_register = (j,j,left_part, "", right_part)
                       
                            if new_register not in total_registers[j]:
                                total_registers[j].append(new_register)
                                
                                if verbose:
                                    print("Adding ")
                                    print(new_register)
             
            """ Step 3. Advance: For all register (i,j,A,\alpha,c|gamma) in REGISTERS[j] 
            where c is a terminal symbol that appears in the position j of u,
            create the register (i,j+1,A,\alpha,c,\gamma) and insert it in REGISTERS[j+1]
            j = j+1 """
            
            if verbose:
                print("Advance")
            
            
            next_registers = [] # REGISTERS[j+1]
            
            for register in total_registers[j]:
                if len(register[4]) > 0:
                    if register[4][0] == word[j]:
                        new_register = (register[0], j+1, register[2], register[3] + word[j], register[4][1:])
                        next_registers.append(new_register)
                        
                        if verbose:
                            print("Adding ")
                            print(new_register)

            
            total_registers.append(next_registers) # append REGISTERS[j+1]
            j = j+1
            
            """Step 4. Termination: For each par of registers of the form (i,j,A,\alpha,\epsilon) in REGISTERS[j]
            and (h,i,B,\gamma, A\delta) in REGISTERS[i], create the new register (h,j,B,\gammaA,\delta) 
            and insert it into REGISTERS[j]"""
            
            if verbose:
                print("Termination")
            
            for first_register in total_registers[j]: # register (i,j,A,\alpha, \epsilon)
                if len(first_register[4]) == 0:
                    for i in range(j):
                        for second_register in total_registers[i]:
                            if second_register[1] == first_register[0] and len(second_register[4]) > 0:
                                if second_register[4][0] == first_register[2]: # register (h,i,B,\gamma,A\delta)
                                    new_register = (second_register[0], j, second_register[2], second_register[3] + first_register[2], second_register[4][1:])
                                    total_registers[j].append(new_register)
                                    
                                    if verbose:
                                        print("Adding ")
                                        print(new_register)
                                    
        """The word can be generated by the grammar if, and only if, in REGISTERS[n], there is a register of the form (0,n,S,\alpha, \epsilon)"""
    
        register_found = False
        i = 0
        
        while not register_found and i < len(total_registers[length_word]):
            register = total_registers[length_word][i]
            
            if register[0] == 0 and register[2] == start_symbol and len(register[4]) == 0:
                register_found = True
                
                if verbose:
                    print("The word can be generated by the grammar because of the register ")
                    print(register)
                
            else:
                i = i+1
            
        
        return register_found
    # Print the object printing each one of the elements of the grammar   


    
    def __str__(self):
        print ("Variable symbols: ")
        print(self.__variable_symbols)
        
        print ("Start symbol: ")
        print(self.__start_symbol)
    
        print ("Terminal symbols: ")
        print(self.__terminal_symbols)
    
        print ("Production Rules: ")
        
        for rule in self.__production_rules:
            print(rule)
            
        return ""
    
    
