# -*- coding: utf-8 -*-
"""
Created on Tue Nov  7 18:17:12 2023

@author: Serafin
"""


class ProductionRule:
    __left_part: str # the left part of the production
    __right_part: [str]
    
    def __init__(self, left, right):
        self.__left_part = left
        self.__right_part = right
    
    def getLeftPart(self):
        return self.__left_part
    
    def getRightPart(self):
        return self.__right_part
    
    def __str__(self):
        print("Left part: ")
        print(self.__left_part)
        
        print("Right part: ")
        print(self.__right_part)
        
        return ""
    
    