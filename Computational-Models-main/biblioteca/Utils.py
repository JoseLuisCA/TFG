# -*- coding: utf-8 -*-
"""
Created on Mon Nov 11 09:47:56 2024

@author: EquipoAsus
"""


def getPowerset(some_set):
        """Returns all subsets of size 0 - len(some_list) for some_list"""
        if len(some_set) == 0:
            return [[]]

        subsets = []
        first_element = some_set[0]
        remaining_set = some_set[1:]
        
        # Strategy: get all the subsets of remaining_list. For each
        # of those subsets, a full subset list will contain both
        # the original subset as well as a version of the subset
        # that contains first_element
        
        for partial_subset in getPowerset(remaining_set):
            subsets.append(partial_subset)
            subsets.append(partial_subset[:] + [first_element])

        return subsets

"Extract a list from a line given the separator and the key character"

def extractSubsetFromLine(line, separator, key_character):
    elements = []
    
    key_found = False
    i = 1
    
    while not key_found:
        if line[i] == key_character:
            key_found = True
            
        i = i+1
        
    line_elements = line[i:-2] # skip until the character { in the line, remove the last character '}'
    list_elements_read = line_elements.split(separator)
    num_elements_read = len(list_elements_read)
                
    for i in range(num_elements_read):
        elements.append(list_elements_read[i].strip())
    
    return elements

"Create a string with the elements of a list given a separator"

def createStringList(list_name, my_list, separator):
    string = list_name + " = {"
    num_elements = len(my_list)
    
    if num_elements > 0:
        for i in range(num_elements -1):
            string = string + my_list[i] + separator
        
        string+=my_list[num_elements - 1]
         
    string += "}"
    
    return string