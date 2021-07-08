#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jan 17 21:51:29 2021
@author: JGSnyder
@email: jakegsnyder43@gmail.com
File of Strings -> File of Strings
Converts VM lines of text to asm lines of text
Code built as part of nand2tetris class on https://www.coursera.org/learn/build-a-computer/
"""

class AssemblyTable(object):
    def __init__(self):
        self.symbols = {
                        'SP':0,
                        'LCL':1,
                        'ARG':2,
                        'THIS':3,
                        'THAT':4,
                        'R0':0,
                        'R1':1,
                        'R2':2,
                        'R3':3,
                        'R4':4,
                        'R5':5,
                        'R6':6,
                        'R7':7,
                        'R8':8,
                        'R9':9,
                        'R10':10,
                        'R11':11,
                        'R12':12,
                        'R13':13,
                        'R14':14,
                        'R15':15,
                        'SCREEN':16384,
                        'KBD':24576
                        }  

    def contains(self, symbol):
        """
        String -> Boolean
        """
        return symbol in self.symbols

    def get_entry(self, symbol):
        return self.symbols[symbol]