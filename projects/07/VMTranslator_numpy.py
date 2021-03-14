import numpy as np
import regex as re
import sys 
import os 

push_pop = {"push", "pop"}
segments = {"local": "@LCL", "argument": "@ARG", "this": "@THIS", "that": "@THAT"}

def checkIgnoreLine(line):
    # Checks if line meets conditions to ignore
    ignoreLine = False

    if not line: # Empty strings are falsy
        ignoreLine = True
    elif line[0]=="/" or line[0]=="\n":
        ignoreLine = True

    return ignoreLine

def memoryTranslate(file_name: str, stack_op: str, command: str, value: str):
    
    line_array = np.empty(0)      # Stores machine code of this vm line 

    value = str(value)

    if command == "pointer":
        if value == "0":
            variable = segments["this"]       
        else:
            variable = segments["that"]

    if stack_op == "push":
        if command in segments.keys():
                line_array = np.append(line_array, [f"{segments[command]}", "D=M", f"@{value}", "A=A+D", "D=M", "@SP", "A=M", "M=D"])
        elif command == "constant":
            line_array = np.append(line_array, [f"@{value}", "D=A", "@SP", "A=M", "M=D"])
        elif command == "static":
            line_array = np.append(line_array, [f"@{file_name}.{value}", "D=M", "@SP", "A=M", "M=D"])
        elif command == "pointer":
            line_array = np.append(line_array, [f"{variable}", "D=M", "@SP", "A=M", "M=D"])
        elif command == "temp":
            line_array = np.append(line_array, [f"@{str(5 + int(value))}", "D=M", "@SP", "A=M", "M=D"])

        line_array = np.append(line_array, ["@SP", "M=M+1"])

    if stack_op == "pop":
        line_array = np.append(line_array, ["@SP", "M=M-1"])

        if command in segments.keys():
            line_array = np.append(line_array, [f"{segments[command]}", "D=M", f"@{value}", "D=A+D", "@R13", "M=D", "@SP", "A=M", "D=M", "@R13", "A=M", "M=D"])
        elif command == "static":
            line_array = np.append(line_array, ["A=M", "D=M", f"@{file_name}.{value}", "M=D"])
        elif command == "pointer":
            line_array = np.append(line_array, ["A=M", "D=M", f"{variable}", "M=D"])
        elif command == "temp":
            line_array = np.append(line_array, ["A=M", "D=M", f"@{str(5 + int(value))}", "M=D"])
    
    return line_array


def arithmetic(count: int, command: str):
    """
    """
    
    line_array = np.empty(0)      # Stores machine code of this vm line 
    eqJump = "eqJump"
    gtJump = "gtJump"
    ltJump = "ltJump"

    count = str(count)

    if command == "add":
        line_array = np.append(line_array, ["@SP", "AM=M-1", "D=M", "@SP", "AM=M-1", "M=D+M"])
    elif command == "sub":
        line_array = np.append(line_array, ["@SP", "AM=M-1", "D=M", "@SP", "AM=M-1", "M=M-D"])
    elif command == "neg":
        line_array = np.append(line_array, ["@SP", "AM=M-1", "M=-M"])
    elif command == "eq":
        line_array = np.append(line_array, ["@SP", "AM=M-1", "D=M", "@SP", "AM=M-1", "D=M-D", "M=-1", f"@{eqJump + count}", "D;JEQ", "@SP", "A=M", "M=0", f"({eqJump + count})"])
    elif command == "gt":
        line_array = np.append(line_array, ["@SP", "AM=M-1", "D=M", "@SP", "AM=M-1", "D=M-D", "M=-1", f"@{gtJump + count}", "D;JGT", "@SP", "A=M", "M=0", f"({gtJump + count})"])
    elif command == "lt":
        line_array = np.append(line_array, ["@SP", "AM=M-1", "D=M", "@SP", "AM=M-1", "D=M-D", "M=-1", f"@{ltJump + count}", "D;JLT", "@SP", "A=M", "M=0", f"({ltJump + count})"])
    elif command == "and":
        line_array = np.append(line_array, ["@SP", "AM=M-1", "D=M", "@SP", "AM=M-1", "M=M&D"])
    elif command == "or":
        line_array = np.append(line_array, ["@SP", "AM=M-1", "D=M", "@SP", "AM=M-1", "M=M|D"])
    elif command == "not":
        line_array = np.append(line_array, ["@SP", "AM=M-1", "M=!M"])

    line_array = np.append(line_array, ["@SP", "M=M+1"])

    return line_array

def translate(machine_code, file_name, file_in):
    """ Determines what type of command each vm line contains and calls functions accordingly

    Args:
        machine_code (np array) :   Resultant hack commands from each line of file_in
        file_name (str)         :   Name of input file
        file_in (str)           :   String of input vm file

    Returns:
        Machine code array based on input vm file
    """

    arith_count = 0 # Arithmetic counter

    for line in file_in:

        commentPos = line.find('/')
        line = line[0:commentPos].strip() # Remove comment and outer whitespace
        if checkIgnoreLine(line):
            continue

        commands = re.split(" ", line.replace("\n",""))

        machine_code = np.append(machine_code, f"// {line}")

        if commands[0] in push_pop:
            machine_code = np.append(machine_code, memoryTranslate(file_name, commands[0], commands[1], commands[2]))
        else:
            machine_code = np.append(machine_code, arithmetic(arith_count, commands[0]))
            arith_count = arith_count + 1

    return machine_code

# This allows you to run the script through command line
if __name__ == "__main__":

    # Do OS pathing for submission
    arg1 = sys.argv[1] 

    file_in = f"{arg1}"
    file_name = os.path.basename(arg1)[:-3]
    file_out = f"{os.path.join(os.path.dirname(arg1), file_name)}.asm"

    file_read = open(file_in, "r")
    machine_code = np.empty(0)      # Stores machine code

    machine_code = translate(machine_code, file_name, file_read)    

    np.savetxt(file_out, machine_code, fmt="%s")