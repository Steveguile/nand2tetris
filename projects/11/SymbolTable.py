
import enum

DICT_NAME = "name"
DICT_TYPE = "type"
DICT_KIND = "kind"
DICT_COUNT = "count"

class SymbolKinds(enum.Enum):
    KIND_NONE = 0
    KIND_STATIC = 1
    KIND_FIELD = 2
    KIND_ARG = 3
    KIND_VAR = 4

SUBROUTINE_VAR_DECS = SymbolKinds.KIND_ARG, SymbolKinds.KIND_VAR

class SymbolTable:
    def __init__(self):
        # lazy, lots of loops but easy
        self.class_table = []
        self.sub_table = []

    def startSubroutine(self):
        self.sub_table = []

    def define(self, name: DICT_NAME, sym_type: DICT_TYPE, kind: SymbolKinds):        
        if kind in "var":
            kind = "local"
        symbol = {DICT_NAME: name, DICT_TYPE: sym_type, DICT_KIND: kind, DICT_COUNT: self.varCount(kind)}
        
        if kind in ["static", "field", "this"]:
            self.class_table.append(symbol.copy())
        else:
            self.sub_table.append(symbol.copy())

    def varCount(self, sym_kind: DICT_KIND):
        count = 0
        table = []

        if sym_kind in ["static", "field"]:
            table = self.class_table
        else:
            table = self.sub_table

        for symbol in table:
            if symbol.get(DICT_KIND) in sym_kind:
                    count = count + 1

        return count

    ''' Could do callback functions for this loop but nvm
    '''
    def exists(self, name: DICT_NAME):
        exists = False

        for symbol in self.sub_table:
            if symbol.get(DICT_NAME) == name:
                exists = True
                break
        
        if not exists: 
            for symbol in self.class_table:
                if symbol.get(DICT_NAME) == name:
                    exists = True
                    break

        return exists

    def kindOf(self, name: DICT_NAME):
        kind = ""

        for symbol in self.sub_table:
            if symbol.get(DICT_NAME) == name:
                kind = symbol.get(DICT_KIND)
                break
        
        if not kind: 
            for symbol in self.class_table:
                if symbol.get(DICT_NAME) == name:
                    kind = symbol.get(DICT_KIND)
                    break

        return kind

    def typeOf(self, name: DICT_NAME):
        sym_type = ""

        for symbol in self.sub_table:
            if symbol.get(DICT_NAME) == name:
                sym_type = symbol.get(DICT_TYPE)
                break

        if not sym_type:
            for symbol in self.class_table:
                if symbol.get(DICT_NAME) == name:
                    sym_type = symbol.get(DICT_TYPE)
                    break

        return sym_type

    def indexOf(self, name: DICT_NAME):
        index = -1    

        for symbol in self.sub_table:
            if symbol.get(DICT_NAME) == name:
                index = symbol.get(DICT_COUNT)
                break

        if index == -1:
            for symbol in self.class_table:
                if symbol.get(DICT_NAME) == name:
                    index = symbol.get(DICT_COUNT)
                    break

        return index