import xml.etree.ElementTree as ET
import xml.dom.minidom as DM
import html

class_var_dec_tokens = {"static", "field"}
type_tokens = {"int", "char", "boolean"}
subroutine_dec_tokens = {"constructor", "function", "method"}
op = {"+", "-", "*", "/", "&", "|", "<", ">", "="}
unary_op = {"-", "~"}
keyword_constant = {"true", "false", "null", "this"}

class CompilationEngine:
    def __init__(self, in_file: str):

        self.compile_out = []
        self.xml_out = ""
        self.tokens = []
        self.token_position = 0

        # Assign file to array
        self.tokens = open(in_file).read().splitlines()            
        self.tokens = self.tokens[1:-1] # Remove <tokens> tags

        # Start compilation process
        self.compileClass()

        # Convert to xml
        self.xml_out = DM.parseString(''.join(self.compile_out)).toprettyxml(indent="")
        self.xml_out = self.xml_out.strip("<?xml version=\"1.0\" ?>").strip() # Gross but keep for coursera matching

    def eat(self, eat_string: str = ""):
        """ Standard eat, move + 1 
        """
        current_token = ET.fromstring(self.tokens[self.token_position])
        if current_token.text not in eat_string and eat_string:
            print(f"current_token '{current_token.text}' of tag '{current_token.tag}' is not one of '{eat_string}'")
        else:
            # Keep token tags in append
            # Lazy method of doing this
            self.compile_out.append(f"<{current_token.tag}> ")
            self.compile_out.append(html.escape(current_token.text))
            self.compile_out.append(f" </{current_token.tag}>")

        # Move counter to next token
        self.token_position = self.token_position + 1

    def compileClass(self):
        """ 'class' className '{' classVarDec* subRoutineDec* '}'
        """
        self.compile_out.append("<class>")
        self.eat("class")

        # ClassName
        #self.compile_out.append("<className>")
        self.eat()
        #self.compile_out.append("</className>")

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

        self.compile_out.append("</class>")

    def compileClassVarDec(self):
        """ ('static'|'field') type varName (',' varName)* ';'
        """
        self.compile_out.append("<classVarDec>")
        self.eat(class_var_dec_tokens)
        self.eat()

        # (',' varName)* ';'
        while True:
            current_token = ET.fromstring(self.tokens[self.token_position])
            # We've stopped reading off variables for this type
            if current_token.text == ";":
                self.eat(";") # Read the ";"
                break
            else:
                self.eat()

        self.compile_out.append("</classVarDec>")

    def compileSubroutineDec(self):
        """ ('constructor'|'function'|'method') ('void'|type) 
            subroutineName '(' parameterList ')' subroutineBody
        """
        self.compile_out.append("<subroutineDec>")
        self.eat(subroutine_dec_tokens)
        # void | type
        self.eat()

        # subroutineName
        self.eat()

        self.eat("(")
        self.compileParameterList()
        self.eat(")")

        self.compileSubroutineBody()

        self.compile_out.append("</subroutineDec>")

    def compileParameterList(self):
        """ ((type varName) (',' type varName)*)?
        """        
        self.compile_out.append("<parameterList>")

        current_token = ET.fromstring(self.tokens[self.token_position]).text
        if current_token != ")":
            self.eat()
            self.eat()
            
            current_token = ET.fromstring(self.tokens[self.token_position]).text
            while current_token == ",":
                self.eat(",")
                self.eat()
                self.eat()
                current_token = ET.fromstring(self.tokens[self.token_position]).text

        self.compile_out.append("</parameterList>")

    def compileSubroutineBody(self):
        """ '{' varDec* statements '}'
        """
        self.compile_out.append("<subroutineBody>")

        self.eat("{")

        # varDec*
        current_token = ET.fromstring(self.tokens[self.token_position]).text
        while current_token == "var":
            self.compileVarDec()
            current_token = ET.fromstring(self.tokens[self.token_position]).text

        # statements
        self.compileStatements()

        self.eat("}")

        self.compile_out.append("</subroutineBody>")

    def compileVarDec(self):
        """ 'var' type varName (',' varName)* ';'
        """
        self.compile_out.append("<varDec>")

        # 'var'
        self.eat("var")
        # type
        self.eat()
        # varName
        self.eat()

        # (',' varName)* ';'
        while True:
            current_token = ET.fromstring(self.tokens[self.token_position])
            # We've stopped reading off variables for this type
            if current_token.text == ";":
                self.eat(";") # Read the ";"
                break
            else:
                self.eat()

        self.compile_out.append("</varDec>")

    def compileStatements(self):
        self.compile_out.append("<statements>")

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

        self.compile_out.append("</statements>")

    def compileLet(self):
        """ 'let' varName ('[' expression ']')? '=' expression ';'
        """
        self.compile_out.append("<letStatement>")

        # 'let'
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

        self.eat(";")

        self.compile_out.append("</letStatement>")

    def compileIf(self):
        self.compile_out.append("<ifStatement>")

        self.eat("if")
        self.eat("(")
        self.compileExpression()
        self.eat(")")
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

        self.compile_out.append("</ifStatement>")

    def compileWhile(self):
        self.compile_out.append("<whileStatement>")

        self.eat("while")
        self.eat("(")
        self.compileExpression()
        self.eat(")")
        self.eat("{")
        self.compileStatements()
        self.eat("}")

        self.compile_out.append("</whileStatement>")

    def compileDo(self):
        self.compile_out.append("<doStatement>")

        self.eat("do")
        
        # subroutineName of subroutineCall
        self.eat()

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
            self.eat("(")
            self.compileExpressionList()
            self.eat(")") 

        self.eat(";")

        self.compile_out.append("</doStatement>")

    def compileReturn(self):
        self.compile_out.append("<returnStatement>")

        self.eat("return")

        current_token = ET.fromstring(self.tokens[self.token_position]).text
        while current_token != ";":
            self.compileExpression()
            current_token = ET.fromstring(self.tokens[self.token_position]).text

        self.eat(";")

        self.compile_out.append("</returnStatement>")

    def compileExpression(self):
        """ term (op term)*
        """
        self.compile_out.append("<expression>")

        self.compileTerm()

        # Grammar says (op term)* but think should be (op term)?
        current_token = ET.fromstring(self.tokens[self.token_position]).text
        while current_token in op:
            self.eat(op)
            self.compileTerm()
            current_token = ET.fromstring(self.tokens[self.token_position]).text

        self.compile_out.append("</expression>")

    def compileTerm(self):
        """ integerConstant | stringConstant | keywordConstant | 
            varName | varName '[' expression ']' | subroutineCall |
            '(' expression ')' | unaryOp term
        """
        self.compile_out.append("<term>")

        current_token = ET.fromstring(self.tokens[self.token_position]).text
        
        # unaryOp term
        if current_token in unary_op:
            self.eat(unary_op)
            self.compileTerm()
        elif current_token in keyword_constant: # keywordConstant
            self.eat(keyword_constant)
        elif current_token == "(": # '(' expression ')'
            self.eat("(")
            self.compileExpression()
            self.eat(")") 
        else: # integerConstant | stringConstant | subroutineCall | varName | varName '[' expression ']'
            self.eat()

            current_token = ET.fromstring(self.tokens[self.
            token_position]).text 
            # '[' expression ']' part of varName '[' expression ']'
            if current_token == "[":
                self.eat("[")
                self.compileExpressionList()
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

        self.compile_out.append("</term>")

    def compileExpressionList(self):
        """ (expression (',' expression)*)?
        """
        self.compile_out.append("<expressionList>")

        current_token = ET.fromstring(self.tokens[self.token_position]).text 
        # Not empty expressionList ( -> ')'
        if current_token != ")":
            self.compileExpression()
            current_token = ET.fromstring(self.tokens[self.token_position]).text 
            while current_token == ",":
                self.eat(",")
                self.compileExpression()
                current_token = ET.fromstring(self.tokens[self.token_position]).text 


        self.compile_out.append("</expressionList>")

