#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jan 17 21:51:29 2021
@author: JGSnyder
@email: jakegsnyder43@gmail.com
File of Strings -> File of Strings in Binary
Converts lines of text into lines of binary
Code built as part of nand2tetris class on https://www.coursera.org/learn/build-a-computer/
"""
from io import StringIO
import sys, os, re, logging

def main():
    if len(sys.argv) != 2:
        print("Usage: python hack_assembler.py <inputfile.asm>")
    else:
        logging.basicConfig(filename='../logs/hack_assembler.log', level=logging.DEBUG)

        # read text into memory as a list
        inf = sys.argv[1]
        in_text = file_read(inf)
    
        # three passes of list, plus symbol assignment
        filtered_list = first_pass(in_text)
        symbols = symbol_parse(filtered_list)
        filtered_list = [line for line in filtered_list if line[0] != "("]

        #iterate thru A and C instructions, convert to binary, continue to build symbols list with variables
        var_mem_location = 16
        for line in filtered_list:
            instruction = commandType(line)
            try:
                if instruction == 'A-instruction':
                    binary_line, symbols, var_mem_location = parse_A(line, symbols, var_mem_location)
                elif instruction == 'C-instruction':
                    binary_line = parse_C(line)
            except Exception:
                logging.exception('Error in parse function.')
            
            out_list = []
            out_list.append(binary_line)

        #format as string, write to file
        out_string = '\n'.join(out_list)
        file_write(out_string)

def file_read(inf):
    """
    File -> List of strings
    Returns list from sys.argv[1]
    """
    try:
        file = open(inf, "r")
        in_text = file.readlines()
        return in_text
    except FileNotFoundError as fnf_error:
        print(fnf_error)
        sys.exit()

def first_pass(in_text):
    """
    ListofStrings -> ListofStrings
    Removes comments(separate lines and in-line) and blank lines from list of strings
    >>> first_pass(["@43", "//this is a program", "", "M=D", ''])
    ['@43', 'M=D']
    >>> first_pass(['', "", "   ", "  @43  "])
    ['@43']
    >>> first_pass(["@43", "(LOOP)", "//this is a program", "", "M=D//test", ''])
    ['@43', '(LOOP)', 'M=D']
    """
    comment = "//"
    filtered_list = [line.split(comment)[0].strip() for line in in_text if line.strip() if line[0:2] != comment]
    return filtered_list

def symbol_parse(in_text):
    """
    List of Strings -> Dict
    Returns 2x dictionaries of values from parsed list of strings
    >>> symbol_parse(["(LOOP)", "@i", "M=D", "(STOP)", "@4", "D=A"])
    {'LOOP': 0, 'STOP': 2}
    >>> symbol_parse(["@sum", "D=A", "@test", "M=AM", "(LOOP)", "@i", "D=M;JEQ", "@sum", "@i"])
    {'LOOP': 4}
    >>> symbol_parse(["@R0", "M;JMP", "(LOOP)", "@i", "M=D", "(STOP)", "@4", "D=A"])
    {'LOOP': 2, 'STOP': 4}
    """
    symbols = {}
    lineNumber = 0
    for line in in_text:
        if line.startswith("("):
            symbol = line.strip("()")
            symbols[symbol] = lineNumber
        else:
            lineNumber += 1
    return symbols

def commandType(line):
    """
    String -> String
    Determines what type of instruction you wrote (A/C)
    >>> commandType("@43")
    'A-instruction'
    >>> commandType("M=D")
    'C-instruction'
    >>> commandType("M = D")
    'C-instruction'
    """
    if line.startswith("@"):
        instruction = 'A-instruction'
        return instruction
    else:
        instruction = 'C-instruction'
        return instruction

def parse_A(instruction, symbols, var_mem_location):
    """
    String, Dict -> String in binary, Dict
    Returns A-instruction in binary, updates Dict of symbols
    >>> parse_A('@3', {}, 16)
    ('0000000000000011', {}, 16)
    >>> parse_A('@sum', {'LOOP': 2}, 16)
    ('0000000000010000', {'LOOP': 2, 'sum': 16}, 17)
    >>> parse_A('@LOOP', {'END': 10, 'LOOP': 2}, 16)
    ('0000000000000010', {'END': 10, 'LOOP': 2}, 16)
    >>> parse_A('@R2', {'LOOP': 2}, 16)
    ('0000000000000010', {'LOOP': 2}, 16)
    """
    predefined_symbols = {
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
    op_code = '0'
    num = instruction[1:]

    if num.isdigit():
        mem_addr = int(num)
    elif num in predefined_symbols.keys():
        mem_addr = predefined_symbols[num]
    elif num in symbols.keys():
        mem_addr = symbols[num]
    else:
        symbols[num] = var_mem_location
        var_mem_location += 1
        mem_addr = symbols[num]

    rest_code = bin(mem_addr)[2:].zfill(15)
    return op_code + rest_code, symbols, var_mem_location

def parse_C(instruction):
    """
    String -> 16 Char String in Binary
    Returns C-instruction in binary
    >>> parse_C('M=D')
    '1110001100001000'
    >>> parse_C('AD=M;JEQ')
    '1111110000110010'
    >>> parse_C('AD=M;JMP')
    '1111110000110111'
    >>> parse_C('0;JMP')
    '1110101010000111'
    >>> parse_C('ADHD=M;JEQ')
    """
    if ';' not in instruction:
        instruction += ";null"
    instruction_split = re.split(r'[;=]', instruction)
    
    if '=' not in instruction:
        instruction_split.insert(0,'null')

    op_code = '111'
    if 'M' in instruction_split[1]:
        a='1'
        instruction_split[1] = instruction_split[1].replace('M', 'A')
    else:
        a='0'

    comp_binary = comp(instruction_split[1])
    dest_binary = dest(instruction_split[0])
    jump_binary = jump(instruction_split[2])
    
    try:
        return op_code + a + comp_binary + dest_binary + jump_binary
    except Exception as e:
        logging.exception(e)

def dest(dest_instruction):
    """
    String -> 3 Char String in binary
    Converts to binary by looking up possibilities in table
    >>> dest('M')
    '001'
    >>> dest('D')
    '010'
    >>> dest('AM')
    '101'
    >>> dest('AMD')
    '111'
    >>> dest('ADDING')
    >>> dest('AM.')
    """
    dest_table = {
        'null':'000',
        'M':'001',
        'D':'010',
        'MD':'011',
        'A':'100',
        'AM':'101',
        'AD':'110',
        'AMD':'111'
    }
    try:
        return dest_table[dest_instruction]
    except KeyError:
        logging.exception('KeyError in dest function')

def comp(comp_instruction):
    """
    String -> 6 Char String in binary
    Converts to binary by looking up possibilities in table, adds 'a' op-code of 0 or 1 if M is in instruction
    >>> comp('1')
    '111111'
    >>> comp('A')
    '110000'
    >>> comp('D&A')
    '000000'
    >>> comp('D&A.')
    """
    comp_table = {
        '0':'101010',
        '1':'111111',
        '-1':'111010',
        'D':'001100',
        'A':'110000',
        '!D':'001101',
        '!A':'110001',
        '-D':'001111',
        '-A':'110011',
        'D+1':'011111',
        'A+1':'110111',
        'D-1':'001110',
        'A-1':'110010',
        'D+A':'000010',
        'D-A':'010011',
        'A-D':'000111',
        'D&A':'000000',
        'D|A':'010101'
    }
    try:
        return comp_table[comp_instruction]
    except KeyError:
        logging.exception('KeyError in comp function')

def jump(jump_instruction):
    """
    String -> 3 Char String in binary
    Converts to binary by looking up possibilities in table
    >>> jump('null')
    '000'
    >>> jump('JGT')
    '001'
    >>> jump('JMP')
    '111'
    >>> jump('JUMP')
    """
    jump_table = {
        'null':'000',
        'JGT':'001',
        'JEQ':'010',
        'JGE':'011',
        'JLT':'100',
        'JNE':'101',
        'JLE':'110',
        'JMP':'111'
    }
    try:
        return jump_table[jump_instruction]
    except KeyError:
        logging.exception('KeyError in jump function')

def file_write(out_string):
    """
    String in Memory -> String in File
    Writes string to file
    """
    filename = os.path.splitext(sys.argv[1])[0]
    ext = '.hack'
    with open(filename + ext, 'w') as writer:
        writer.write(out_string)
    
if __name__ == '__main__':
    main()
    #import doctest
    #print(doctest.testmod(verbose=False))