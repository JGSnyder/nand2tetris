import unittest
from VMTranslator import Parser, CodeWriter

class ParserTest_command_type(unittest.TestCase):
    def test_command_type_push(self):
        p = Parser('push static 0')
        self.assertEqual(Parser.command_type(p), 'C_PUSH')

    def test_command_type_pop(self):
        p = Parser('pop constant 2')
        self.assertEqual(Parser.command_type(p), 'C_POP')

    def test_command_type_arithmetic_add(self):
        p = Parser('add\n')
        self.assertEqual(Parser.command_type(p), 'C_ARITHMETIC')

    def test_command_type_arithmetic_sub(self):
        p = Parser('sub')
        self.assertEqual(Parser.command_type(p), 'C_ARITHMETIC')

    def test_command_type_label(self):
        p = Parser('label hello //substitutes something')
        self.assertEqual(Parser.command_type(p), 'C_LABEL')

    def test_command_type_goto(self):
        p = Parser('goto loop check')
        self.assertEqual(Parser.command_type(p), 'C_GOTO')

    def test_command_type_if(self):
        p = Parser('if-goto loop')
        self.assertEqual(Parser.command_type(p), 'C_IF')

class ParserTest_arg1(unittest.TestCase):
    def test_arg1_push(self):
        p = Parser('push static 0')
        self.assertEqual(Parser.arg1(p), 'push')

    def test_arg1_pop(self):
        p = Parser('pop static 0')
        self.assertEqual(Parser.arg1(p), 'pop')

    def test_arg1_add(self):
        p = Parser('add ')
        self.assertEqual(Parser.arg1(p), 'add')

    def test_arg1_gt(self):
        p = Parser('gt')
        self.assertEqual(Parser.arg1(p), 'gt')

class ParserTest_arg2(unittest.TestCase):
    def test_arg2_push_static(self):
        p = Parser('push static 0')
        self.assertEqual(Parser.arg2(p), 'static')

    def test_arg2_push_local(self):
        p = Parser('push local 2//this is a test\n')
        self.assertEqual(Parser.arg2(p), 'LCL')

    def test_arg2_label(self):
        p = Parser('label LOOP\n')
        self.assertEqual(Parser.arg2(p), 'LOOP')

class ParserTest_arg3(unittest.TestCase):
    def test_arg3(self):
        p = Parser('push static 2//this is a test\n')
        self.assertEqual(Parser.arg3(p), 2)

    def test_push_local(self):
        p = Parser('push local 5\n')
        self.assertEqual(Parser.arg3(p), 5)

class CodeWriterTest_asm_arithmetic(unittest.TestCase):
    def test_asm_arithmetic_add(self):
        c = CodeWriter('Foo')
        self.assertEqual(CodeWriter.asm_arithmetic(c,'add'), '@SP\nM=M-1\nA=M\nD=M\n@SP\nM=M-1\nA=M\nM=M+D\n@SP\nM=M+1\n')

    def test_asm_arithmetic_sub(self):
        c = CodeWriter('Foo')
        self.assertEqual(CodeWriter.asm_arithmetic(c,'sub'), '@SP\nM=M-1\nA=M\nD=M\n@SP\nM=M-1\nA=M\nM=M-D\n@SP\nM=M+1\n')

    def test_asm_arithmetic_and(self):
        c = CodeWriter('Foo')
        self.assertEqual(CodeWriter.asm_arithmetic(c,'and'), '@SP\nM=M-1\nA=M\nD=M\n@SP\nM=M-1\nA=M\nM=M&D\n@SP\nM=M+1\n')

    def test_asm_arithmetic_or(self):
        c = CodeWriter('Foo')
        self.assertEqual(CodeWriter.asm_arithmetic(c,'or'), '@SP\nM=M-1\nA=M\nD=M\n@SP\nM=M-1\nA=M\nM=M|D\n@SP\nM=M+1\n')

    def test_asm_arithmetic_neg(self):
        c = CodeWriter('Foo')
        self.assertEqual(CodeWriter.asm_arithmetic(c,'neg'), '@SP\nM=M-1\nA=M\nM=-M\n@SP\nM=M+1\n')

    def test_asm_arithmetic_not(self):
        c = CodeWriter('Foo')
        self.assertEqual(CodeWriter.asm_arithmetic(c,'not'), '@SP\nM=M-1\nA=M\nM=!M\n@SP\nM=M+1\n')

    def test_asm_arithmetic_gt(self):
        c = CodeWriter('Foo')
        self.assertEqual(CodeWriter.asm_arithmetic(c,'gt'), 
                        "@SP\n" \
                        "M=M-1\n" \
                        "A=M\n" \
                        "D=M\n" \
                        "@SP\n" \
                        "M=M-1\n" \
                        "A=M\n" \
                        "D=M-D\n" \
                        "@OUTPUT_TRUE_0\n" \
                        "D;JGT\n" \
                        "D=0\n" \
                        "@NEXT_COMMAND_0\n" \
                        "0;JMP\n" \
                        \
                        "(OUTPUT_TRUE_0)\n" \
                        "D=-1\n" \
                        "@NEXT_COMMAND_0\n" \
                        "0;JMP\n" \
                        \
                        "(NEXT_COMMAND_0)\n" \
                        "@SP\n" \
                        "A=M\n" \
                        "M=D\n" \
                        "@SP\n" \
                        "M=M+1\n"
        )

    def test_asm_arithmetic_lt(self):
        c = CodeWriter('Foo')
        self.assertEqual(CodeWriter.asm_arithmetic(c,'lt'),
                        "@SP\n" \
                        "M=M-1\n" \
                        "A=M\n" \
                        "D=M\n" \
                        "@SP\n" \
                        "M=M-1\n" \
                        "A=M\n" \
                        "D=M-D\n" \
                        "@OUTPUT_TRUE_0\n" \
                        "D;JLT\n" \
                        "D=0\n" \
                        "@NEXT_COMMAND_0\n" \
                        "0;JMP\n" \
                        \
                        "(OUTPUT_TRUE_0)\n" \
                        "D=-1\n" \
                        "@NEXT_COMMAND_0\n" \
                        "0;JMP\n" \
                        \
                        "(NEXT_COMMAND_0)\n" \
                        "@SP\n" \
                        "A=M\n" \
                        "M=D\n" \
                        "@SP\n" \
                        "M=M+1\n"
        )
class CodeWriterTest_asm_othercommands(unittest.TestCase):

    def test_asm_pushpop(self):
        c = CodeWriter('Foo')
        self.assertEqual(CodeWriter.asm_pushpop(c,'pop', 'static', '2'), '@Foo.static2\nD=A\n@addr\nM=D\n@SP\nM=M-1\nA=M\nD=M\n@addr\nA=M\nM=D\n')

    def test_asm_pushpop_first_lines(self):
        c = CodeWriter('Foo')
        self.assertEqual(CodeWriter.pushpop_firstlines(c,'testfile.bar', ''), '@testfile.bar\nD=A\n')

    def test_asm_label(self):
        c = CodeWriter('Foo')
        self.assertEqual(CodeWriter.asm_label(c,'LOOP'), '(Foo.main$LOOP)\n')

    def test_asm_goto(self):
        c = CodeWriter('Foo')
        self.assertEqual(CodeWriter.asm_goto(c,'LOOP'), '@Foo.main$LOOP\n0;JMP\n')

    def test_asm_if(self):
        c = CodeWriter('Foo')
        self.assertEqual(CodeWriter.asm_if(c,'LOOP'), 
                        "@SP\n" \
                        "M=M-1\n" \
                        "A=M\n" \
                        "D=M\n" \
                        "@Foo.main$LOOP\n" \
                        "D; JNE\n" \
                        )

    def test_asm_function_1localvar(self):
        c = CodeWriter('Foo')
        self.assertEqual(CodeWriter.asm_function(c, 'bar', 1),
                        "(Foo.bar)\n" \
                        "@0\n" \
                        "D=A\n" \
                        "@SP\n" \
                        "A=M\n" \
                        "M=D\n" \
                        "@SP\n" \
                        "M=M+1\n")

    def test_asm_function_2localvar(self):
        c = CodeWriter('Foo')
        self.assertEqual(CodeWriter.asm_function(c, 'bar', 2),
                        "(Foo.bar)\n" \
                        "@0\n" \
                        "D=A\n" \
                        "@SP\n" \
                        "A=M\n" \
                        "M=D\n" \
                        "@SP\n" \
                        "M=M+1\n" \
                        "@0\n" \
                        "D=A\n" \
                        "@SP\n" \
                        "A=M\n" \
                        "M=D\n" \
                        "@SP\n" \
                        "M=M+1\n")

    def test_asm_callfunction(self):
        c = CodeWriter('testfile')
        self.maxDiff = None
        self.assertEqual(CodeWriter.asm_call(c, 'bar', 2),
                        "@testfile.bar$ret.0\n" \
                        "@0\n" \
                        "D=A\n" \
                        "@SP\n" \
                        "A=M\n" \
                        "M=D\n" \
                        "@SP\n" \
                        "M=M+1\n" \
                        "@0\n" \
                        "D=A\n" \
                        "@SP\n" \
                        "A=M\n" \
                        "M=D\n" \
                        "@SP\n" \
                        "M=M+1\n")

if __name__ == '__main__':
    unittest.main()