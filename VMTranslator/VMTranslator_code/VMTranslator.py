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
import sys, os, re, logging
import AssemblyTable

def main():
    assert len(sys.argv) == 2, "Usage: python VMTranslator.py <inputfile.vm>"
    logging.basicConfig(filename='logs/VMTranslator.log', level=logging.DEBUG)

    inf = sys.argv[1] #01/FunctionDirectory/Function.vm
    filename = os.path.splitext(os.path.basename(inf))[0] + '.asm' #Function.asm
    code = CodeWriter(filename)
    try:
        if inf.endswith('.vm'):
            filepath = os.path.splitext(inf)[0] + '.asm' #/01/FunctionDirectory/Function.asm
            with open(filepath, 'w') as outf:
                #write initial setup code
                outf.write(code.asm_init())
                translateFile(code, inf, outf)

        elif os.path.isdir(inf): #FunctionDirectory
            if inf.endswith('/'):
                inf = inf[0:-1] #../main/ -> ../main
            filepath = inf + '/' + filename #01/FunctionDirectory/FunctionDirectory.asm
            with open(filepath, 'w') as outf:
                #write initial setup code
                outf.write(code.asm_init())
                for file in os.listdir(inf):
                    if file.endswith('.vm'):
                        translateFile(code, inf + '/' + file, outf)
                        code.staticsCounter += 1
        else:
            logging.exception("Error opening file.", exc_info=True)
    #TODO not logging properly
    except PermissionError:
        logging.exception("You do not have the appropriate permissions. Run chmod a+x on the file you are working with and try again.")
    except FileNotFoundError:
        logging.exception("The file was not found. Please try again.")

def translateFile(code, inf, outf):
    line_no = 0
    #parse each line, convert, and write to outf
    for line in open(inf, 'r'):
        try:
            p = Parser(line)
            if p.line == '': #ignore empty lines
                continue
            elif p.command_type() == 'C_ARITHMETIC':
                commandString = code.asm_arithmetic(p.arg1())
            elif p.command_type() in ('C_PUSH', 'C_POP'):
                commandString = code.asm_pushpop(p.arg1(), p.arg2(), p.arg3())
            elif p.command_type() == 'C_LABEL':
                commandString = code.asm_label(p.arg2())
            elif p.command_type() == 'C_GOTO':
                commandString = code.asm_goto(p.arg2())
            elif p.command_type() == 'C_IF':
                commandString = code.asm_if(p.arg2())
            elif p.command_type() == 'C_FUNCTION':
                commandString = code.asm_function(p.arg2(), p.arg3())
            elif p.command_type() == 'C_CALL':
                commandString = code.asm_call(p.arg2(), p.arg3())
            elif p.command_type() == 'C_RETURN':
                commandString = code.asm_return()
            else:
                commandString = ""
        except Exception:
            logging.exception(f"Error on {inf} line {line_no}.")

        #increment line count and write to file
        else:
            line_no += 1
            if p.line:
                if not p.line.startswith("//"):
                    outf.write("\n//" + line + commandString)
                else:
                    outf.write(line)
    """
    infinite loop addition for early nand2tetris tests
    outf.write("\n(INFINITE_LOOP)\n" \
                "@INFINITE_LOOP\n"
                "0;JMP")
    """

class Parser(object):
    def __init__(self, line):
        #removes comments and extra space
        self.line = re.sub("(//).+", "", line).strip()

    def command_type(self):
        command_types = {'push': 'C_PUSH', 'pop': 'C_POP', ('add', 'sub', 'neg', 'eq', 'gt', 'lt', 'and', 'or', 'not'): 'C_ARITHMETIC', 
        'label': 'C_LABEL', 'goto': 'C_GOTO', 'if-goto': 'C_IF', 'function': 'C_FUNCTION', 'return': 'C_RETURN', 'call': 'C_CALL'}
        try:
            return next(v for k, v in command_types.items() if self.arg1() in k)
        except Exception:
            logging.exception("Not a valid command type.")

    def arg1(self):
        """
        String -> String
        """
        return self.line.strip().split()[0]
    
    def arg2(self):
        """
        String -> String
        Returns 'static' in push static i OR 'LCL' in pop local i
        """
        memory_abbreviations = {'local': 'LCL', 'argument': 'ARG', 'this': 'THIS', 'that': 'THAT'}
        var = self.line.split()[1] # 'static' or 'constant'
        return memory_abbreviations[var] if var in memory_abbreviations else var
    
    def arg3(self):
        """
        String -> Int
        Returns i in 'push constant i' or 'pop static i'
        """
        return int(self.line.split()[2])

class CodeWriter(object):
    def __init__(self, filename):
        self.compareCounter = 0 #increments every time two stack numbers are compared; ensures no duplicate variable names
        self.callCounter = 0 #increments every time function is called; ensures no duplicate function names
        self.staticsCounter = 0 #increments every time new '.vm' file is opened for translation; ensures no duplicate static names
        self.filename = filename #argument passed to CodeWriter
        self.function_name = '' #necessary to create label_name
        self.label_name = self.filename + '.' + self.function_name #once code object is created
                                                                    #this label_name does not update
        self.fixed_memory_locations = AssemblyTable.AssemblyTable()
        self.additional_memory_locations = {'pointer': 3, 'temp': 5}

    def asm_init(self):
        init_setup_lines = "//Startup code\n" \
                            "@256\n" \
                            "D=A\n" \
                            "@SP\n" \
                            "M=D\n" \
                            "@700\n" \
                            "D=A\n" \
                            "@LCL\n" \
                            "M=D\n" \
                            "@800\n" \
                            "D=A\n" \
                            "@ARG\n" \
                            "M=D\n" \
                            "@900\n" \
                            "D=A\n" \
                            "@THIS\n" \
                            "M=D\n" \
                            "@1000\n" \
                            "D=A\n" \
                            "@THAT\n" \
                            "M=D\n" + \
                            self.asm_call('Sys.init', 0)
        return init_setup_lines

    def asm_arithmetic(self, arg1):
        if arg1 == 'add':
            return self.combine_op('+')
        elif arg1 == 'sub':
            return self.combine_op('-')
        elif arg1 == 'and':
            return self.combine_op('&')
        elif arg1 == 'or':
            return self.combine_op('|')
        elif arg1 == 'neg':
            return self.single_op('-')
        elif arg1 == 'not':
            return self.single_op('!')
        elif arg1 in ('gt', 'lt', 'eq'):
            return self.compare_op(arg1)
        else:
            logging.exception('Improper arithmetic command used.')

    def single_op(self,operator):
        convertedLine = "@SP\n" \
                        "M=M-1\n" \
                        "A=M\n" \
                        "M=" + operator + "M\n" \
                        "@SP\n" \
                        "M=M+1\n"
        return convertedLine

    def combine_op(self,operator):
        convertedLine = "@SP\n" \
                        "M=M-1\n" \
                        "A=M\n" \
                        "D=M\n" \
                        "@SP\n" \
                        "M=M-1\n" \
                        "A=M\n" \
                        "M=M" + operator + "D\n" \
                        "@SP\n" \
                        "M=M+1\n"
        return convertedLine

    def compare_op(self, operator):
        convertedLine = "@SP\n" \
                        "M=M-1\n" \
                        "A=M\n" \
                        "D=M\n" \
                        "@SP\n" \
                        "M=M-1\n" \
                        "A=M\n" \
                        "D=M-D\n" \
                        "@OUTPUT_TRUE_" + str(self.compareCounter) + "\n" \
                        "D;J" + operator.upper() + "\n" \
                        "D=0\n" \
                        "@NEXT_COMMAND_" + str(self.compareCounter) + "\n" \
                        "0;JMP\n" \
                        \
                        "(OUTPUT_TRUE_" + str(self.compareCounter) + ")" + "\n" \
                        "D=-1\n" \
                        "@NEXT_COMMAND_" + str(self.compareCounter) + "\n" \
                        "0;JMP\n" \
                        \
                        "(NEXT_COMMAND_" + str(self.compareCounter) + ")" + "\n" \
                        "@SP\n" \
                        "A=M\n" \
                        "M=D\n" \
                        "@SP\n" \
                        "M=M+1\n"
        self.compareCounter += 1
        return convertedLine

    def arg2_memory_location(self,arg2):
        """
        String -> Int
        """
        if self.fixed_memory_locations.contains(arg2):
            return self.fixed_memory_locations.get_entry(arg2)
        elif arg2 in ('pointer', 'temp'):
            return self.additional_memory_locations[arg2]
        else:
            pass

    def pushpop_firstlines(self, arg2, arg3):
        if arg2 in ('LCL', 'ARG', 'THIS', 'THAT'):
            first_lines = "@" + str(arg3) + "\n" \
                            "D=A\n" \
                            "@" + str(self.arg2_memory_location(arg2)) + "\n" \
                            "D=M+D\n"
        elif arg2 == 'constant':
            first_lines = "@" + str(arg3) + "\n" \
                            "D=A\n"
        elif arg2 == 'static':
            first_lines = "@" + self.filename + "." + 'static' + str(self.staticsCounter) + str(arg3) + "\n" \
                            "D=A\n"
        elif arg2 in ('temp', 'pointer'):
            first_lines = "@" + str(arg3) + "\n" \
                            "D=A\n" \
                            "@" + str(self.arg2_memory_location(arg2)) + "\n" \
                            "D=A+D\n"
        else:
            first_lines = "@" + arg2 + "\n" \
                            "D=A\n"
        return first_lines

    def asm_pushpop(self, arg1, arg2, arg3):
        if arg1 == 'push':
            if arg2 == 'constant':
                second_lines = "@SP\n" \
                            "A=M\n" \
                            "M=D\n" \
                            "@SP\n" \
                            "M=M+1\n"
            else:
                second_lines = "@addr\n" \
                            "M=D\n" \
                            "A=M\n" \
                            "D=M\n" \
                            "@SP\n" \
                            "A=M\n" \
                            "M=D\n" \
                            "@SP\n" \
                            "M=M+1\n"
            return self.pushpop_firstlines(arg2, arg3) + second_lines
        elif arg1 == 'pop':
            second_lines = "@addr\n" \
                            "M=D\n" \
                            "@SP\n" \
                            "M=M-1\n" \
                            "A=M\n" \
                            "D=M\n" \
                            "@addr\n" \
                            "A=M\n" \
                            "M=D\n"
            return self.pushpop_firstlines(arg2, arg3) + second_lines

    def asm_label(self, arg2):
        """
        label label
        """
        return "(" + self.label_name + arg2 + ")\n"

    def asm_goto(self, arg2):
        """
        goto label
        """
        return "@" + self.label_name + arg2 + "\n" \
                "0;JMP\n"

    def asm_if(self, arg2):
        """
        if-goto label
        """
        convertedLine = "@SP\n" \
                        "M=M-1\n" \
                        "A=M\n" \
                        "D=M\n" \
                        "@" + self.label_name + arg2 + "\n" \
                        "D; JNE\n"
        return convertedLine

    def asm_function(self, arg2, arg3):
        """
        function function_name nVars
        """
        self.function_name = arg2
        return "(" + self.filename + '.' + self.function_name + ")\n" + \
                (arg3 * self.asm_pushpop('push','constant', 0)) # push constant 0 as LCL variables arg3 times

    def save_mem_space(self):
        """
        pushes memory address to top of the stack
        """
        return "@SP\n" \
                "A=M\n" \
                "M=D\n" \
                "@SP\n" \
                "M=M+1\n"

    def asm_call(self, arg2, arg3):
        """
        call function_name nArgs
        """
        self.function_name = arg2
        self.callCounter +=1
        retAddr = self.filename + '.' + self.function_name +'$ret.' + str(self.callCounter)
        save_caller_frame = "//call. save_caller_frame\n" + \
                            "@" + retAddr + "\n" \
                            "D=A\n" + \
                            self.save_mem_space() + \
                            \
                            "//call. push local\n" + \
                            "@LCL\n" \
                            "D=M\n" + \
                            self.save_mem_space() + \
                            \
                            "//call. push ARG\n" + \
                            "@ARG\n" \
                            "D=M\n" + \
                            self.save_mem_space() + \
                            \
                            "//call. push THIS\n" + \
                            "@THIS\n" \
                            "D=M\n" + \
                            self.save_mem_space() + \
                            \
                            "//call. push THAT\n" + \
                            "@THAT\n" \
                            "D=M\n" + \
                            self.save_mem_space()
        set_new_arg =   "//call. set_new_arg\n" \
                        "@SP\n" \
                        "D=M\n" \
                        "@" + str(arg3 + 5) + "\n" \
                        "D=D-A\n" \
                        "@ARG\n" \
                        "M=D\n"
        set_new_lcl =   "//call. set_new_lcl\n" \
                        "@SP\n" \
                        "D=M\n" \
                        "@LCL\n" \
                        "M=D\n"
        goto_called_function = self.asm_goto(arg2)
       
        return save_caller_frame + set_new_arg + set_new_lcl + goto_called_function + "(" + retAddr + ")"

    def restore_mem_space(self, pointer):
        """
        only used for asm_return function to restore locations in callee's stack to caller's original memory values
        """
        restored_pointer = "@endframe\n" \
                            "M=M-1\n" \
                            "A=M\n" \
                            "D=M\n" \
                            "@" + pointer + "\n" \
                            "M=D\n"
        return restored_pointer

    def asm_return(self):
        """
        return
        """
        endframe_equals_lcl = "@LCL\n" \
                                "D=M\n" \
                                "@endframe\n" \
                                "M=D\n"
        retAddr_designation = "@5\n" \
                                "D=A\n" \
                                "@endframe\n" \
                                "D=M-D\n" \
                                "A=D\n" \
                                "D=M\n" \
                                "@retAddr\n" \
                                "M=D\n"
        pop_arg_zero = self.asm_pushpop('pop', 'ARG', 0)
        move_sp = "@ARG\n" \
                    "D=M+1\n" \
                    "@SP\n" \
                    "M=D\n"
        #THAT, THIS, ARG, LCL needs to be in this order for the restore_mem_space function to work properly
        #since THAT = *(endframe-1), THIS = *(endframe-2), etc.
        restore_that = self.restore_mem_space("THAT")
        restore_this = self.restore_mem_space("THIS")
        restore_arg = self.restore_mem_space("ARG")
        restore_lcl = self.restore_mem_space("LCL")
        goto_retaddr = "@retAddr\n" \
                        "A=M\n" \
                        "0;JMP\n"

        return endframe_equals_lcl + retAddr_designation + pop_arg_zero + move_sp + \
                restore_that + restore_this + restore_arg + restore_lcl + goto_retaddr

if __name__ == '__main__':
    main()