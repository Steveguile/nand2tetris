import numpy as np
import regex as re

STARTADDRESS = 16 # First 16 are already assigned

comp_dict = {
    "0"     : "0101010",
    "1"     : "0111111",
    "-1"    : "0111010",
    "D"     : "0001100",
    "A"     : "0110000",
    "!D"    : "0001101",
    "!A"    : "0110001",
    "-D"    : "0001111",
    "-A"    : "0110011",
    "D+1"   : "0011111",
    "A+1"   : "0110111",
    "D-1"   : "0001110",
    "A-1"   : "0110010",
    "D+A"   : "0000010",
    "D-A"   : "0010011",
    "A-D"   : "0000111",
    "D&A"   : "0000000",
    "D|A"   : "0010101",
    "M"     : "1110000",
    "!M"    : "1110001",
    "-M"    : "1110011",
    "M+1"   : "1110111",
    "M-1"   : "1110010",
    "D+M"   : "1000010",
    "D-M"   : "1010011",
    "M-D"   : "1000111",
    "D&M"   : "1000000",
    "D|M"   : "1010101"
}
dest_dict = {
    "null"  : "000",
    "M"     : "001",
    "D"     : "010",
    "A"     : "100",
    "MD"    : "011",
    "AM"    : "101",
    "AD"    : "110",
    "AMD"   : "111"
}
jump_dict = {
    "null"  : "000",
    "JGT"   : "001",
    "JEQ"   : "010",
    "JGE"   : "011",
    "JLT"   : "100",
    "JNE"   : "101",
    "JLE"   : "110",
    "JMP"   : "111"
}

def addPredefinedAddress(symbol_table):
    # Sets up default symbols in symbol table
    for number in range(STARTADDRESS):
        symbol_table["R" + str(number)] = number
        symbol_table[str(number)] = number # Not just @RX but @X

    symbol_table["SCREEN"] = 16384
    symbol_table["KBD"] = 24576
    symbol_table["SP"] = 0
    symbol_table["LCL"] = 1
    symbol_table["ARG"] = 2
    symbol_table["THIS"] = 3
    symbol_table["THAT"] = 4

    return symbol_table

def checkIgnoreLine(line):
    # Checks if line meets conditions to ignore
    ignoreLine = False

    if not line: # Empty strings are falsy
        ignoreLine = True
    elif line[0]=="/" or line[0]=="\n":
        ignoreLine = True

    return ignoreLine

def checkSkipInstruction(line, instruction_type):
    # Checks an instruction based on instruction type
    # Types are:
    #               * 'i' for jump instruction such as (XXX)
    #               * 'a' for address such as @XXX
    skipInstruction = True
    if line[0]=="(" and instruction_type=="i":
        skipInstruction = False
    elif line[0]=="@" and instruction_type=="a":
        skipInstruction = False

    return skipInstruction

def firstPass(symbol_table, file_read, truncated_file):
    # Adds any jump instruction '(XXX)' to the symbol table
    # Outputs a truncated version of in file for reduced line range
    currentAddress = STARTADDRESS - 1 # Starts at 0
    lineNumber = 0 # current line for jump instruction

    for line in file_read:

        commentPos = line.find('/')
        line = line[0:commentPos].strip() # Remove comment and outer whitespace
        if checkIgnoreLine(line):
            continue

        # Store asm line in new file buffer
        truncated_file = np.append(truncated_file, line.replace("\n",""))

        if checkSkipInstruction(line, "i"):
            lineNumber += 1
            continue

        line = line[1:-1]
        symbol_table[line] = lineNumber

    return symbol_table, truncated_file

def aInstruction(line, symbol_table, memAddress):

    # Add symbol to table and create machine code
    if line[1:] not in symbol_table:
        # If symbol is an exact address (@30) then use this as the address
        if line[1].isnumeric():
            symbol_table[line[1:]] = int(line[1:])
        # Otherwise increment from 16
        else: 
            memAddress += 1
            symbol_table[line[1:]] = memAddress

    # Make address binary and pad to 16 bit ([2:] because bin() indicates binary type by starting with 0b)
    instruction = bin(symbol_table[line[1:]])[2:].zfill(16)

    return instruction, memAddress

def cInstruction(line):

    splitline = re.split('=|;', line)

    # If there is a destination there cannot be a jump and visa versa
    if line.find("=") != -1:
        instruction = f"111{comp_dict[splitline[1]]}{dest_dict[splitline[0]]}000"
    elif line.find(";") != -1:
        instruction = f"111{comp_dict[splitline[0]]}000{jump_dict[splitline[1]]}"

    return instruction

def secondPass(machine_code, symbol_table, truncated_file):

    memAddress = STARTADDRESS - 1 

    for line in truncated_file:
        if line[0] == "@":
            aResult, memAddress = aInstruction(line, symbol_table, memAddress)
            machine_code = np.append(machine_code, aResult)
        elif line[0] != "(": # Do something with this later and move to else
            machine_code = np.append(machine_code, cInstruction(line))

    return machine_code


# This allows you to run the script through command line
if __name__ == "__main__":
    
    file_dir = "pong"
    file_name = "Pong"
    file_in = f"{file_dir}/{file_name}.asm"
    file_out = f"{file_dir}/{file_name}.hack"

    file_read = open(file_in, "r")
    machine_code = np.empty(0)      # Stores machine code
    truncated_file = np.empty(0)    # Stores file_read lines that contain .asm code (not blank or comments)
    symbol_table = {}  # Stores symbols for address lookup
    symbol_table = addPredefinedAddress(symbol_table)

    symbol_table, truncated_file = firstPass(symbol_table, file_read, truncated_file)
    machine_code = secondPass(machine_code, symbol_table, truncated_file)

    #print(truncated_file)
    #print(symbol_table)
    #print(machine_code)

    np.savetxt(file_out, machine_code, fmt="%s")










