import xml.etree.ElementTree as ET
import xml.dom.minidom as DM
import html
import sys
import time
from SymbolTable import SymbolTable, SymbolKinds
from VMWriter import VMWriter 

class CompilationEngine:
    def __init__(self, in_file: str, compile_out_name: str):

        self.tokens = []
        self.token_pos = 0
        self.label_count = -1 # to start at 0
        self.symbol_table = SymbolTable()
        self.class_name = ""
        self.sub_name = ""

        # Debug var
        self.current_compile = ""

        # Assign file to array
        self.tokens = open(in_file).read().splitlines()            
        self.tokens = self.tokens[1:-1] # Remove <tokens> tags

        self.vm_writer = VMWriter(compile_out_name)

        # Start compilation process
        self.compileClass()
        self.vm_writer.close()


    def eat(self, eat_string: str):
        """ Standard eat, move + 1 for token text
        """
        token_content = ""

        current_token = ET.fromstring(self.tokens[self.token_pos])
        if current_token.text not in eat_string:
            print(f"current_token '{current_token.text}' of tag '{current_token.tag}' is not one of '{eat_string}'")
            print(f"current call: {self.current_compile}")
            sys.exit(1)
        else:
            token_content = current_token.text
            self.token_pos = self.token_pos + 1

        return token_content

    def eatTag(self, eat_tag: str):
        """ Standard eat, move + 1 for token tag
        """
        token_content = ""

        current_token = ET.fromstring(self.tokens[self.token_pos])

        if current_token.tag not in eat_tag:
            print(f"current_token tag '{current_token.tag}' with text '{current_token.text}' is not one of '{eat_tag}'")
            print(f"current call: {self.current_compile}")
            sys.exit(1)
        else:
            token_content = current_token.text
            self.token_pos = self.token_pos + 1

        return token_content

    def currentToken(self):
        return ET.fromstring(self.tokens[self.token_pos])

    def currentTokenEquals(self, string_list: str):
        """ eats if current token element is one of a list of options
        """
        equals = False

        if self.currentToken().text in string_list:
            equals = True

        return equals

    def currentTokenTagEquals(self, string_list: str):
        """ eats if current token element is one of a list of options
        """
        equals = False

        if self.currentToken().tag in string_list:
            equals = True

        return equals

    def compileClass(self):
        """ 'class' className '{' classVarDec* subRoutineDec* '}'
        """
        self.current_compile = "compileClass"
        self.eat("class")
        self.class_name = self.eatTag("identifier")
        self.eat("{")

        while self.currentTokenEquals(["field", "static"]):
            self.compileClassVarDec()

        while self.currentTokenEquals(["constructor", "function", "method"]):
            self.compileSubroutineDec()

        self.eat("}")
        
    def compileClassVarDec(self):
        """ ('static'|'field') type varName (',' varName)* ';'
        """
        self.current_compile = "compileClassVarDec"
        symbol_kind = self.eat(["field", "static"])
        symbol_type = self.eatTag(["keyword", "identifier"])
        symbol_name = self.eatTag("identifier")
        self.symbol_table.define(symbol_name, symbol_type, symbol_kind)
        
        while self.currentTokenEquals(","):
            self.eat(",")
            symbol_name = self.eatTag("identifier")
            self.symbol_table.define(symbol_name, symbol_type, symbol_kind)

        self.eat(";")

    def compileSubroutineDec(self):
        """ ('constructor'|'function'|'method') ('void'|type) 
            subroutineName '(' parameterList ')' subroutineBody
        """        
        self.current_compile = "compileSubroutineDec"
        self.symbol_table.startSubroutine() # Initialise subroutine symbol table

        symbol_kind = self.eat(["constructor", "function", "method"])
        symbol_type = self.eatTag(["identifier", "keyword"])
        self.sub_name = self.eatTag("identifier")

        if symbol_kind == "method":
            self.symbol_table.define("this", symbol_type, "argument")

        self.eat("(")
        self.compileParameterList()
        self.eat(")")

        self.compileSubroutineBody(symbol_kind)

    def compileParameterList(self):
        """ ((type varName) (',' type varName)*)?
        """        
        self.current_compile = "compileParameterList"
        symbol_kind = "argument" 
        
        while not self.currentTokenEquals(")"):
            symbol_type = self.eatTag("keyword")
            symbol_name = self.eatTag("identifier")
            self.symbol_table.define(symbol_name, symbol_type, symbol_kind)
            if not self.currentTokenEquals(","):
                break
            self.eat(",")

    def compileSubroutineBody(self, sub_kind: str):
        """ '{' varDec* statements '}'
        """
        self.current_compile = "compileSubroutineBody"
        self.eat("{")

        while self.currentTokenEquals("var"):
            self.compileVarDec()

        self.vm_writer.writeFunction(f"{self.class_name}.{self.sub_name}", self.symbol_table.varCount("local"))

        # Special handling for return of these
        if sub_kind == "constructor":
            self.vm_writer.writePush("constant", self.symbol_table.varCount("field"))
            self.vm_writer.writeCall("Memory.alloc", 1)
            self.vm_writer.writePop("pointer", 0)
        elif sub_kind == "method":
            self.vm_writer.writePush("argument", 0)
            self.vm_writer.writePop("pointer", 0)

        self.compileStatements()

        self.eat("}")

    def compileVarDec(self):
        """ 'var' type varName (',' varName)* ';'
        """
        self.current_compile = "compileVarDec"
        symbol_kind = self.eat("var")
        symbol_type = self.eatTag(["keyword", "identifier"])
        symbol_name = self.eatTag("identifier")
        self.symbol_table.define(symbol_name, symbol_type, symbol_kind)

        while not self.currentTokenEquals(";"):
            self.eat(",")
            symbol_name = self.eatTag("identifier")
            self.symbol_table.define(symbol_name, symbol_type, symbol_kind)

        self.eat(";")

    def compileStatements(self):
        self.current_compile = "compileStatements"
        while not self.currentTokenEquals("}"):
            if self.currentTokenEquals("let"):
                self.compileLet()
            elif self.currentTokenEquals("if"):
                self.compileIf()
            elif self.currentTokenEquals("while"):
                self.compileWhile()
            elif self.currentTokenEquals("do"):
                self.compileDo()
            elif self.currentTokenEquals("return"):
                self.compileReturn()

    def compileLet(self):
        """ 'let' varName ('[' expression ']')? '=' expression ';'
        """
        self.current_compile = "compileLet"
        self.eat("let")
        symbol_name = self.eatTag("identifier")
        
        if self.currentTokenEquals("["):
            self.vm_writer.writePush(self.symbol_table.kindOf(symbol_name), self.symbol_table.indexOf(symbol_name))
            self.eat("[")
            self.compileExpression()
            self.eat("]")
            self.vm_writer.writeArithmetic("add")
            self.eat("=")
            self.compileExpression()
            self.eat(";")

            self.vm_writer.writePop("temp", 0)
            self.vm_writer.writePop("pointer", 1)
            self.vm_writer.writePush("temp", 0)
            self.vm_writer.writePop("that", 0)
        # just var
        else:
            self.eat("=")
            self.compileExpression()
            self.eat(";")
            self.vm_writer.writePop(self.symbol_table.kindOf(symbol_name), self.symbol_table.indexOf(symbol_name))

    def compileIf(self):
        self.current_compilecurrent_token = "compileIf"
        self.label_count = self.label_count + 1
        label_count = self.label_count
        self.eat("if")

        self.eat("(")
        self.compileExpression()
        self.eat(")")

        self.vm_writer.writeArithmetic("not")
        self.vm_writer.writeIf(f"IF_RET{label_count}")
        
        self.eat("{")
        self.compileStatements()
        self.eat("}")

        self.vm_writer.writeGoto(f"IF_GOTO{label_count}")
        self.vm_writer.writeLabel(f"IF_RET{label_count}")

        if self.currentTokenEquals("else"):
            self.eat("else")
            self.eat("{")
            self.compileStatements()
            self.eat("}")

        self.vm_writer.writeLabel(f"IF_GOTO{label_count}")

    def compileWhile(self):
        self.current_compilecurrent_token = "compileWhile"
        self.label_count = self.label_count + 1
        label_count = self.label_count
        self.eat("while")
        self.vm_writer.writeLabel(f"WHILE_START{label_count}")
        self.eat("(")
        self.compileExpression()
        self.eat(")")
        self.vm_writer.writeArithmetic("not")
        self.vm_writer.writeIf(f"WHILE_END{label_count}")
        self.eat("{")
        self.compileStatements()
        self.eat("}")

        self.vm_writer.writeGoto(f"WHILE_START{label_count}")
        self.vm_writer.writeLabel(f"WHILE_END{label_count}")

    def compileDo(self):
        self.current_compile = "compileDo"
        self.eat("do")
        
        arguments = 0
        object_name = ""
        function_name = self.eatTag("identifier")

        # function_name is actually object_name
        if self.currentTokenEquals("."):
            self.eat(".")
            object_name = function_name
            function_name = self.eatTag("identifier")

        # Calling function not method
        if not object_name:
            self.vm_writer.writePush("pointer", 0)
            object_name = self.class_name
            arguments = arguments + 1
        # Object declared in symbol table
        elif self.symbol_table.exists(object_name):
            symbol_segment = self.symbol_table.kindOf(object_name)
            symbol_index = self.symbol_table.indexOf(object_name)
            object_name = self.symbol_table.typeOf(object_name)
            self.vm_writer.writePush(symbol_segment, symbol_index)
            arguments = arguments + 1

        self.eat("(")
        arguments = self.compileExpressionList() + arguments
        self.eat(")")

        self.vm_writer.writeCall(f"{object_name}.{function_name}", arguments)
        self.vm_writer.writePop("temp", 0)

        self.eat(";")

    def compileReturn(self):
        self.current_compile = "compileReturn"
        self.eat("return")

        if self.currentTokenEquals(";"):
            self.vm_writer.writePush("constant", 0) # Always push on return
        else:
            self.compileExpression()
                    
        self.eat(";")

        self.vm_writer.writeReturn()

    def compileExpression(self):
        """ term (op term)*
        """
        self.current_compile = "compileExpression"
        op_list = ["+", "-", "*", "/", "&", "|", "<", ">", "="]
        self.compileTerm()

        while self.currentTokenEquals(op_list):
            op = self.eat(op_list)
            self.compileTerm()
            self.vm_writer.writeArithmetic(op)

    def compileTerm(self):
        """ integerConstant | stringConstant | keywordConstant | 
            varName | varName '[' expression ']' | subroutineCall |
            '(' expression ')' | unaryOp term
        """
        self.current_compile = "compileTerm"
        # integerConstant
        if self.currentTokenTagEquals("integerConstant"):
            self.vm_writer.writePush("constant", self.eatTag("integerConstant"))
        # stringConstant
        elif self.currentTokenTagEquals("stringConstant"):
            string = self.eatTag("stringConstant")
            self.vm_writer.writePush("constant", len(string)) 
            self.vm_writer.writeCall("String.new", 1)
            for char in string:
                self.vm_writer.writePush("constant", ord(char))
                self.vm_writer.writeCall("String.appendChar", 2)
        # This, True, False, Null
        elif self.currentTokenTagEquals("keyword"):
            keyword = self.eatTag("keyword")
            if keyword in "this":
                self.vm_writer.writePush("pointer", 0)
            elif keyword in "true":
                self.vm_writer.writePush("constant", 0)
                self.vm_writer.writeArithmetic("not")
            elif keyword in ["false", "null"]:
                self.vm_writer.writePush("constant", 0)
            else:
                print(f"\"{keyword}\" keyword not handled")
                sys.exit(1)
        # ( expression )
        elif self.currentTokenEquals("("):
            self.eat("(")
            self.compileExpression()
            self.eat(")")
        # unaryOp term
        elif self.currentTokenEquals(["~", "-"]):
            unary_op = self.eat(["~", "-"])
            self.compileTerm()
            if unary_op in "~":
                self.vm_writer.writeArithmetic("not")
            else:
                self.vm_writer.writeArithmetic("neg")
        else:
            identifier = self.eatTag("identifier")

            # varName [ expression ]
            if self.currentTokenEquals("["):
                self.vm_writer.writePush(self.symbol_table.kindOf(identifier), self.symbol_table.indexOf(identifier))
                self.eat("[")
                self.compileExpression()
                self.eat("]")
                self.vm_writer.writeArithmetic("add")
                self.vm_writer.writePop("pointer", 1)
                self.vm_writer.writePush("that", 0)
            # function call
            elif self.currentTokenEquals("("):
                self.eat("(")
                arguments = self.compileExpressionList()
                self.eat(")")
                self.vm_writer.writePush("pointer", 0)
                self.writeCall(f"{self.class_name}.{identifier}", arguments + 1)
            # method call
            elif self.currentTokenEquals("."):
                arguments = 0
                self.eat(".")
                method_name = self.eatTag("identifier")
                if self.symbol_table.exists(identifier):
                    symbol_segment = self.symbol_table.kindOf(identifier)
                    symbol_index = self.symbol_table.indexOf(identifier)
                    identifier = self.symbol_table.typeOf(identifier)
                    self.vm_writer.writePush(symbol_segment, symbol_index)
                    arguments = 1
                self.eat("(")
                arguments = self.compileExpressionList() + arguments
                self.eat(")")
                self.vm_writer.writeCall(f"{identifier}.{method_name}", arguments)
            # var
            elif self.symbol_table.exists(identifier):
                self.vm_writer.writePush(self.symbol_table.kindOf(identifier), self.symbol_table.indexOf(identifier))
            # oops
            else:
                print(self.symbol_table.class_table)
                print(self.symbol_table.sub_table)
                print(f"\"{identifier}\" identifier not handled")
                sys.exit(1)

    def compileExpressionList(self):
        """ (expression (',' expression)*)?
        """
        self.current_compile = "compileExpressionList"
        expression_count = 0
        while not self.currentTokenEquals(")"):
            self.compileExpression()
            expression_count = expression_count + 1
            if not self.currentTokenEquals(","):
                break
            self.eat(",")

        return expression_count
