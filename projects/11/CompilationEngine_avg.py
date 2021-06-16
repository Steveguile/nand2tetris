import xml.etree.ElementTree as ET
import xml.dom.minidom as DM
import html
from SymbolTable import SymbolTable, SymbolKinds
from VMWriter import VMWriter 

class_var_dec_tokens = {"static", "field"}
type_tokens = {"int", "char", "boolean"}
subroutine_dec_tokens = {"constructor", "function", "method"}
op = {"+", "-", "*", "/", "&", "|", "<", ">", "="}
unary_op = {"-", "~"}
keyword_constant = {"true", "false", "null", "this"}

class CompilationEngine:
    def __init__(self, in_file: str, compile_out_name: str):

        # self.compile_out = []
        self.tokens = []
        self.token_position = 0
        self.last_tag = ""
        self.last_token = ""
        self.symbol_table = SymbolTable()
        self.class_name = ""
        self.function_type = ""
        self.current_arguments = 0
        self.current_expression = []

        # Assign file to array
        self.tokens = open(in_file).read().splitlines()            
        self.tokens = self.tokens[1:-1] # Remove <tokens> tags

        self.vm_writer = VMWriter(compile_out_name)

        # Start compilation process
        self.compileClass()
        self.vm_writer.close()

    def eat(self, eat_string: str = "", force_tag: str = ""):
        """ Standard eat, move + 1 
        """
        current_token = ET.fromstring(self.tokens[self.token_position])
        if current_token.text not in eat_string and eat_string:
            print(f"current_token '{current_token.text}' of tag '{current_token.tag}' is not one of '{eat_string}'")
        else:
            # Keep token tags in append
            # Lazy method of doing this
            self.last_token = html.escape(current_token.text)
            
            # Force tag from symbol table or keep?
            if not force_tag:
                self.last_tag = self.symbol_table.kindOf(self.last_token)
                # If not in symbol table then choose current token tag
                if not self.last_tag:
                    self.last_tag = current_token.tag
            else:
                self.last_tag = force_tag

        # Move counter to next token
        self.token_position = self.token_position + 1

    def eatForce(self, force_tag):
        self.eat("", force_tag)

    def compileClass(self):
        """ 'class' className '{' classVarDec* subRoutineDec* '}'
        """
        self.eat("class")

        # ClassName
        self.eat()
        self.class_name = self.last_token
        self.eat("{")

        # Compile one or more classVarDec or subRoutineDec
        while True:
            current_token = ET.fromstring(self.tokens[self.token_position]).text
            if current_token in class_var_dec_tokens:
                self.compileClassVarDec()
            elif current_token in subroutine_dec_tokens:
                self.compileSubroutineDec()
            else:
                # No more, we leave
                break

        self.eat("}")

    def compileClassVarDec(self):
        """ ('static'|'field') type varName (',' varName)* ';'
        """
        self.eat(class_var_dec_tokens)
        symbol_kind = self.last_token
        self.eat()
        symbol_type = self.last_token

        # (',' varName)* ';'
        while True:
            current_token = ET.fromstring(self.tokens[self.token_position])
            # We've stopped reading off variables for this type
            if current_token.text == ";":
                self.eat(";") # Read the ";"
                break
            else:
                # "," or varName
                if current_token.text == ",":
                    self.eat()
                else:
                    self.eatForce(symbol_kind)
                    self.symbol_table.define(self.last_token, symbol_type, symbol_kind)

    def compileSubroutineDec(self):
        """ ('constructor'|'function'|'method') ('void'|type) 
            subroutineName '(' parameterList ')' subroutineBody
        """
        # Initialise starts from parameter list - add arguments to symbol table
        self.symbol_table.startSubroutine()

        self.eat(subroutine_dec_tokens)
        if self.last_token == "method":
            # Add "this" to argument list in symbol table
            self.symbol_table.define("this", self.class_name, keyword)
        # void | type
        self.eat()
        self.function_type = self.last_token
        # subroutineName
        self.eat()
        function = self.last_token

        self.eat("(")
        self.compileParameterList()
        self.eat(")")

        params = self.symbol_table.kindOf("argument")
        if not params:
            params = 0
        self.vm_writer.writeFunction(f"{self.class_name}.{function}", params)

        self.compileSubroutineBody()


    def compileParameterList(self):
        """ ((type varName) (',' type varName)*)?
        """        

        keyword = "argument"
        self.param_count = 0

        current_token = ET.fromstring(self.tokens[self.token_position]).text
        while current_token != ")":
            self.eat()
            symbol_type = self.last_token
            self.eatForce(keyword)
            symbol_name = self.last_token
            # Add to symbol table
            self.symbol_table.define(symbol_name, symbol_type, keyword)
            self.param_count = self.param_count + 1
            # Check for another parameter
            current_token = ET.fromstring(self.tokens[self.token_position]).text
            if current_token != ",":
                break
            self.eat(",")

    def compileSubroutineBody(self):
        """ '{' varDec* statements '}'
        """
        self.eat("{")

        # varDec*
        current_token = ET.fromstring(self.tokens[self.token_position]).text
        while current_token == "var":
            self.compileVarDec()
            current_token = ET.fromstring(self.tokens[self.token_position]).text

        # statements
        self.compileStatements()

        self.eat("}")

    def compileVarDec(self):
        """ 'var' type varName (',' varName)* ';'
        """
        self.eat("var")
        symbol_kind = "local"
        # type
        self.eat()
        symbol_type = self.last_token

        # (',' varName)* ';'
        while True:
            current_token = ET.fromstring(self.tokens[self.token_position])
            # We've stopped reading off variables for this type
            if current_token.text == ";":
                self.eat(";") # Read the ";"
                break
            else:
                # "," or varName
                if current_token.text == ",":
                    self.eat()
                else:
                    self.eatForce(symbol_kind)
                    self.symbol_table.define(self.last_token, symbol_type, symbol_kind)

    def compileStatements(self):

        while True:
            current_token = ET.fromstring(self.tokens[self.token_position]).text
            if current_token == "let":
                self.compileLet()
            elif current_token == "if":
                self.compileIf()
            elif current_token == "while":
                self.compileWhile()
            elif current_token == "do":
                self.compileDo()
            elif current_token == "return":
                self.compileReturn()
            else:
                break


    def compileLet(self):
        """ 'let' varName ('[' expression ']')? '=' expression ';'
        """

        self.eat("let")
        # varName
        self.eat()

        # ('[' expression ']')?
        current_token = ET.fromstring(self.tokens[self.token_position]).text
        if current_token == '[':
            self.eat("[")
            self.compileExpression()
            self.eat("]") 
        
        self.eat("=")

        self.compileExpression()

        self.codeWrite(self.current_expression)

        self.eat(";")


    def compileIf(self):

        self.eat("if")
        self.eat("(")
        self.compileExpression()
        self.eat(")")

        self.codeWrite(self.current_expression)

        self.eat("{")
        self.compileStatements()
        self.eat("}")
        
        current_token = ET.fromstring(self.tokens[self.token_position]).text
        while current_token == "else":
            self.eat("else")
            self.eat("{")
            self.compileStatements()
            self.eat("}")
            current_token = ET.fromstring(self.tokens[self.token_position]).text


    def compileWhile(self):

        self.eat("while")
        self.eat("(")
        self.compileExpression()
        self.eat(")")

        self.codeWrite(self.current_expression)

        self.eat("{")
        self.compileStatements()
        self.eat("}")

    def compileDo(self):

        self.eat("do")
        
        # subroutineName or subroutineCall
        self.eat()
        call = self.last_token

        current_token = ET.fromstring(self.tokens[self.token_position]).text
        # subroutineCall - subroutineName '(' expressionList ')'
        if current_token == "(":
            self.eat("(")
            self.compileExpressionList()
            self.eat(")")
        # subroutineCall - (className | varName) '.' subroutineName '(' expressionList ')'
        elif current_token == ".":
            self.eat(".")
            self.eat()
            call = f"{call}.{self.last_token}"
            self.eat("(")
            self.compileExpressionList()
            self.eat(")") 

        self.vm_writer.writeCall(call, self.current_arguments)

        # "do" must pop top most value from stack
        self.vm_writer.writePop("temp", 0)

        self.eat(";")

    def compileReturn(self):

        if self.function_type == "void":
            # Must push something
            self.vm_writer.writePush("constant", 0)

        self.eat("return")
        self.vm_writer.writeReturn()

        current_token = ET.fromstring(self.tokens[self.token_position]).text
        while current_token != ";":
            self.compileExpression()
            current_token = ET.fromstring(self.tokens[self.token_position]).text

        self.eat(";")

    def compileExpression(self):
        """ term (op term)*
        """

        self.compileTerm()

        # Grammar says (op term)* but think should be (op term)?
        current_token = ET.fromstring(self.tokens[self.token_position]).text
        while current_token in op:
            self.current_expression.append(current_token)
            self.eat(op)
            self.compileTerm()
            current_token = ET.fromstring(self.tokens[self.token_position]).text

    def codeWrite(self, expression_list):

        if not expression_list[0].isnumeric():
            # Maybe function? In form of func( or Obj.func(
            if len(expression_list) > 1:
                print(expression_list)
                if (expression_list[1] == "(" or expression_list[3] == "("):
                    start_func = expression_list.index("(")
                    end_func = expression_list.index(")")
                    for i in range(start_func, end_func, 2):
                        self.codeWrite(expression_list[i:])

                    # No args as of yet - wait till it breaks
                    if start_func == 1:
                        self.vm_writer.writeCall(expression_list[0])
                    else:
                        self.vm_writer.writeCall(expression_list[0:2])
                elif expression_list[0] == "(":
                    self.codeWrite(expression_list[1:])
                else: # Varible
                    self.vm_writer.writePush(self.symbol_table.kindOf(expression_list[0]), self.symbol_table.indexOf(expression_list[0]))
            else: # Varible
                self.vm_writer.writePush(self.symbol_table.kindOf(expression_list[0]), self.symbol_table.indexOf(expression_list[0]))
        else:
            if expression_list[0] in unary_op:
                self.codeWrite(expression_list[1:])
                self.vm_writer.writeArithmetic(expression_list[0])
            elif len(expression_list) > 1:
                if expression_list[1] in op:
                    self.codeWrite(expression_list[0])
                    self.codeWrite(expression_list[2:])
                    self.vm_writer.writeArithmetic(expression_list[1])            
                else: 
                    self.vm_writer.writePush("constant", expression_list[0])
            else: 
                self.vm_writer.writePush("constant", expression_list[0])

    def compileTerm(self):
        """ integerConstant | stringConstant | keywordConstant | 
            varName | varName '[' expression ']' | subroutineCall |
            '(' expression ')' | unaryOp term
        """

        current_token = ET.fromstring(self.tokens[self.token_position]).text
        
        # unaryOp term
        if current_token in unary_op:
            self.eat(unary_op)
            self.compileTerm()
        elif current_token in keyword_constant: # keywordConstant
            self.eat(keyword_constant)
        elif current_token == "(": # '(' expression ')'
            self.eat("(")
            self.current_expression.append(self.last_token)
            self.compileExpression()
            self.eat(")") 
            self.current_expression.append(self.last_token)
        else: # integerConstant | stringConstant | subroutineCall | varName | varName '[' expression ']'
            self.eat()
            self.current_expression.append(current_token)

            current_token = ET.fromstring(self.tokens[self.
            token_position]).text 

            # '[' expression ']' part of varName '[' expression ']'
            if current_token == "[":
                self.eat("[")
                self.compileExpression()
                self.eat("]")
            # subroutineCall - subroutineName '(' expressionList ')'
            elif current_token == "(":
                self.eat("(")
                self.eat()
                self.eat(")")
            # subroutineCall - (className | varName) '.' subroutineName '(' expressionList ')'
            elif current_token == ".":
                self.eat(".")
                self.eat()
                self.eat("(")
                self.compileExpressionList()
                self.eat(")") 

    def compileExpressionList(self):
        """ (expression (',' expression)*)?
        """

        self.current_arguments = 0

        current_token = ET.fromstring(self.tokens[self.token_position]).text 
        # Not empty expressionList ( -> ')'
        if current_token != ")":
            self.compileExpression()

            print(self.current_expression)
            self.codeWrite(self.current_expression)

            self.current_arguments = self.current_arguments + 1
            current_token = ET.fromstring(self.tokens[self.token_position]).text 
            while current_token == ",":
                self.eat(",")
                self.compileExpression()

                self.codeWrite(self.current_expression)

                self.current_arguments = self.current_arguments + 1
                current_token = ET.fromstring(self.tokens[self.token_position]).text 

