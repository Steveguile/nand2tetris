import enum
import html

keyword = {"class", "constructor", "function", "method",
           "field", "static", "var", "int", "char", "boolean",
           "void", "true", "false", "null", "this", "let", "do",
           "if", "else","while", "return"}
symbol = {"{", "}", "(", ")", "[", "]", ",", ".", ";", "+", "-",
          "*", "/", "&", "|", "<", ">", "-", "~", "="}
int_max = 32767

class TokenType(enum.Enum):
    NONE = 0
    KEYWORD = 1
    SYMBOL = 2
    IDENTIFIER = 3
    INT_CONST = 4
    STRING_CONST = 5

class JackTokenizer:
    def __init__(self, file_name: str):
        
        self.file_name = file_name
        self.token_array = []
        self.in_string_const = False # Instance attribute check if currently processing string (allow spaces)
        self.advance()

    def checkIgnoreLine(self, line: str):
        """ Determines if a line has characteristics required to ignore \n
        Args: \n
            line    :   Line of .vm code \n
        Returns: \n
            Boolean saying if line should be skipped or not \n
        """
        # Checks if line meets conditions to ignore
        ignoreLine = False

        if not line: # Empty strings are falsy
            ignoreLine = True
        elif line[0]=="/" or line[0] == "*" or line[0]=="\n":
            ignoreLine = True

        return ignoreLine

    def advance(self):

        file_read = open(self.file_name, "r")
        build_token = ""

        self.token_array.append("<tokens>")

        for line in file_read:
            # If blank line or comment - skip
            if self.checkIgnoreLine(line.lstrip()):
                continue

            # Remove CR LF
            line = line.rstrip()

            # Loop through each character 
            for char_pos, char in enumerate(line):

                # if comment at end of line, break
                if line[char_pos:char_pos+2] == "//":
                    break

                build_token = build_token + char
                # Assume we've found a token as next char is invalid
                if not self.hasMoreTokens(line, char_pos):
                    build_token = build_token.strip() # Remove any whitespace
                    # Remove any blank lines (from blanks in between symbols)
                    if build_token:
                        self.token_array.append(self.tokenToXML(build_token, self.tokenType(build_token)))
                    # Reset value
                    build_token = ""
                    continue

        self.token_array.append("</tokens>")

    def hasMoreTokens(self, line, line_pos):

        # If first " token set bool to say we've started string, flip on next occurence
        if line[line_pos] == "\"":
            self.in_string_const = not self.in_string_const

        # Next character
        next_pos = line_pos + 1
        has_tokens = True # Assume has more tokens by default

        # If symbol is next/current character or end of line, current token is over
        if next_pos >= len(line) or line[next_pos] in symbol or line[line_pos] in symbol:
            has_tokens = False
        elif not line[next_pos].strip() and not self.in_string_const:
            has_tokens = False # If we're not in a string then dissalow spaces

        return has_tokens

    def tokenType(self, token):

        token_type = TokenType.NONE

        if token in keyword:
            token_type = TokenType.KEYWORD
        elif token in symbol:
            token_type = TokenType.SYMBOL
        elif token.isnumeric():
            token_type = TokenType.INT_CONST
        elif token[0] == "\"":
            token_type = TokenType.STRING_CONST
        else:
            token_type = TokenType.IDENTIFIER

        return token_type

    def tokenToXML(self, token, token_type):

        # XML elemnt to be returned
        elem = ""

        if token_type == TokenType.KEYWORD:
            elem = f"<keyword>{token}</keyword>"
        elif token_type == TokenType.SYMBOL:
            elem = f"<symbol>{html.escape(token)}</symbol>"
        elif token_type == TokenType.INT_CONST:
            elem = f"<integerConstant>{token}</integerConstant>"
        elif token_type == TokenType.STRING_CONST:
            token = token.strip('"')
            elem = f"<stringConstant>{token}</stringConstant>"
        elif token_type == TokenType.IDENTIFIER:
            #print(self.token_array[len(self.token_array)-1])
            elem = f"<identifier>{token}</identifier>"

        return elem

