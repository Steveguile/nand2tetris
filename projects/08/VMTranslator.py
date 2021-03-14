import sys 
import os 

push_pop_commands = {"push", "pop"}
arithmetic_commands = {"add", "sub", "neg", "eq", "gt", "lt", "and", "or", "not"}
branching_commands = {"label", "if-goto", "goto"}
function_commands = {"function", "call", "return"}
segments = {"local": "@LCL", "argument": "@ARG", "this": "@THIS", "that": "@THAT"}

def checkIgnoreLine(line: str):
    """ Determines if a line has characteristics required to ignore
    Args:
        line    :   Line of .vm code   
    Returns:
        Boolean saying if line should be skipped or not
    """
    # Checks if line meets conditions to ignore
    ignoreLine = False

    if not line: # Empty strings are falsy
        ignoreLine = True
    elif line[0]=="/" or line[0]=="\n":
        ignoreLine = True

    return ignoreLine

def memoryTranslate(file_name: str, command: str, mem_seg: str, value: str):
    """ Determines how to handle a given memory operation command in hack assembly
    Args:
        file_name   :   Name of file currently being converted to hack. Used for static variables
        command     :   Stack operation, see push_pop_commands
        mem_seg     :   Memory segment command applies to, see segments dict
        value       :   Value applied to command and memory segment
    Returns:
        Machine code array corresponding to input command 
    """

    line_array = []      # Stores machine code of this vm line 

    value = str(value)

    if mem_seg == "pointer":
        if value == "0":
            variable = segments["this"]       
        else:
            variable = segments["that"]

    if command == "push":
        if mem_seg in segments.keys():
                line_array.extend([f"{segments[mem_seg]}", "D=M", f"@{value}", "A=A+D", "D=M", "@SP", "A=M", "M=D"])
        elif mem_seg == "constant":
            line_array.extend([f"@{value}", "D=A", "@SP", "A=M", "M=D"])
        elif mem_seg == "static":
            line_array.extend([f"@{file_name}.{value}", "D=M", "@SP", "A=M", "M=D"])
        elif mem_seg == "pointer":
            line_array.extend([f"{variable}", "D=M", "@SP", "A=M", "M=D"])
        elif mem_seg == "temp":
            line_array.extend([f"@{str(5 + int(value))}", "D=M", "@SP", "A=M", "M=D"])

        line_array.extend(["@SP", "M=M+1"])

    if command == "pop":
        line_array.extend(["@SP", "M=M-1"])

        if mem_seg in segments.keys():
            line_array.extend([f"{segments[mem_seg]}", "D=M", f"@{value}", "D=A+D", "@R13", "M=D", "@SP", "A=M", "D=M", "@R13", "A=M", "M=D"])
        elif mem_seg == "static":
            line_array.extend(["A=M", "D=M", f"@{file_name}.{value}", "M=D"])
        elif mem_seg == "pointer":
            line_array.extend(["A=M", "D=M", f"{variable}", "M=D"])
        elif mem_seg == "temp":
            line_array.extend(["A=M", "D=M", f"@{str(5 + int(value))}", "M=D"])
    
    return line_array

def arithmetic(count: int, command: str):
    """ Determines how to handle arithmetic command in hack assembly
    Args:
        count   :   Incremental count to increment and apply to every {eq, gt, lt} 
        command :   Type of arithmetic command, see arithmetic_commands
    Returns:
        Machine code array corresponding to input command 
    """

    line_array = []      # Stores machine code of this vm line 
    eqJump = "eqJump"
    gtJump = "gtJump"
    ltJump = "ltJump"

    count = str(count)
    if command == "add":
        line_array.extend(["@SP", "AM=M-1", "D=M", "@SP", "AM=M-1", "M=D+M"])
    elif command == "sub":
        line_array.extend(["@SP", "AM=M-1", "D=M", "@SP","AM=M-1", "M=M-D"])
    elif command == "neg":
        line_array.extend(["@SP", "AM=M-1", "M=-M"])
    elif command == "eq":
        line_array.extend(["@SP", "AM=M-1", "D=M", "@SP", "AM=M-1", "D=M-D", "M=-1", f"@{eqJump + count}", "D;JEQ", "@SP", "A=M", "M=0", f"({eqJump + count})"])
    elif command == "gt":
        line_array.extend(["@SP", "AM=M-1", "D=M", "@SP", "AM=M-1", "D=M-D", "M=-1", f"@{gtJump + count}", "D;JGT", "@SP", "A=M", "M=0", f"({gtJump + count})"])
    elif command == "lt":
        line_array.extend(["@SP", "AM=M-1", "D=M", "@SP", "AM=M-1", "D=M-D", "M=-1", f"@{ltJump + count}", "D;JLT", "@SP", "A=M", "M=0", f"({ltJump + count})"])
    elif command == "and":
        line_array.extend(["@SP", "AM=M-1", "D=M", "@SP", "AM=M-1", "M=M&D"])
    elif command == "or":
        line_array.extend(["@SP", "AM=M-1", "D=M", "@SP", "AM=M-1", "M=M|D"])
    elif command == "not":
        line_array.extend(["@SP", "AM=M-1", "M=!M"])

    line_array.extend(["@SP", "M=M+1"])

    return line_array

def branching(command: str, label: str):
    """ Determines how to handle brancing command in hack assembly
    Args:
        command :   Type of branching command, see branching_commands
        label   :   Branch label to jump to / set position of 
    Returns:
        Machine code array corresponding to input command 
    """

    line_array = []

    if command == "label":        
        line_array.extend([f"({label})"])
    elif command == "if-goto":
        line_array.extend(["@SP", "AM=M-1", "D=M", f"@{label}", "D;JNE"])
    elif command == "goto":
        line_array.extend(["D=0", f"@{label}", "D;JEQ"])

    return line_array

def func(command: str, name: str, number: str):
    """ Determines how to handle function command in hack assembly
    Args:
        command :   Type of function command, see function_commands 
        name    :   Name of the function
        number  :   Number of arguments/local variables 
    Returns:
        Machine code array corresponding to input command 
    """

    line_array = []

    if command == "function":
        line_array.extend([f"({name})"])                                                        # Generate label
        for local_vars in range(int(number)):                                                   # For every local variable
            line_array.extend([f"// push local 0 for {name}"])
            line_array.extend(memoryTranslate("", "push", "constant", "0"))                     # Call push constant 0
    elif command == "call":
        line_array.extend([f"@RETURN.{name}"])                                                    # Push return address label
        line_array.extend(["@LCL", "D=M", "@SP", "A=M", "M=D", "@SP", "M=M+1"])                  # Push LCL
        line_array.extend(["@ARG", "D=M", "@SP", "A=M", "M=D", "@SP", "M=M+1"])                  # Push ARG
        line_array.extend(["@THIS", "D=M", "@SP", "A=M", "M=D", "@SP", "M=M+1"])                 # Push THIS
        line_array.extend(["@THAT", "D=M", "@SP", "A=M", "M=D", "@SP", "M=M+1"])                 # Push THAT
        line_array.extend([f"@{number}", "D=A", "@5", "D=D+A", "@SP", "D=M-D", "@ARG", "M=D"])  # ARG = SP-(nArgs + 5)
        line_array.extend(["@SP", "D=M", "@LCL", "M=D"])                                        # LCL = SP
        line_array.extend(branching("goto", name))                                              # goto functionname
        line_array.extend([f"(RETURN.{name})"])                                                   # label for return address
    elif command == "return":
        line_array.extend(["@LCL", "D=M", "@endFrame", "M=D"])                                  # endFrame = LCL
        line_array.extend(["@retAddr", "M=D", "@5", "D=A", "@retAddr", "M=M-D"])                # retAddr = (*endFrame - 5)
        line_array.extend(["@SP", "AM=M-1", "D=M", "@ARG", "A=M", "M=D"])                       # *ARG = pop() (get return value (SP-1) onto arg)
        line_array.extend(["@ARG", "D=M", "@SP", "M=D+1"])                                      # SP = ARG + 1
        line_array.extend(["@endFrame", "D=M", "@1", "D=D-A", "A=D", "D=M", "@THAT", "M=D"])    # THAT = (*endFrame - 1)
        line_array.extend(["@endFrame", "D=M", "@2", "D=D-A", "A=D", "D=M", "@THIS", "M=D"])    # THIS = (*endFrame - 2)
        line_array.extend(["@endFrame", "D=M", "@3", "D=D-A", "A=D", "D=M", "@ARG", "M=D"])     # ARG = (*endFrame - 3)
        line_array.extend(["@endFrame", "D=M", "@4", "D=D-A", "A=D", "D=M", "@LCL", "M=D"])     # LCL = (*endFrame - 4)
        line_array.extend(["@retAddr", "A=M"])                                                  # goto retAddr

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

        machine_code.append(f"// {line}")
        line = line.replace("\n","").split(" ")

        if line[0] in push_pop_commands:
            machine_code.extend(memoryTranslate(file_name, line[0], line[1], line[2]))
        elif line[0] in arithmetic_commands:
            machine_code.extend(arithmetic(arith_count, line[0]))
            arith_count = arith_count + 1
        elif line[0] in branching_commands:
            machine_code.extend(branching(line[0], line[1]))
        elif line[0] in function_commands:
            if line[0] == "return":
                line.extend(["", ""]) # Save changings func args, just add empty array elems to return
            machine_code.extend(func(line[0], line[1], line[2]))

    return machine_code

# This allows you to run the script through command line
if __name__ == "__main__":

    # Do OS pathing for submission
    file_in = sys.argv[1].strip("\/")
    file_outpath = os.path.dirname(file_in)
    file_outname = os.path.basename(file_in)
    file_directory = os.path.join(file_outpath, file_outname)
    file_out = f"{os.path.join(file_directory, file_outname)}.asm"

    machine_code = []

    # Process Sys.vm first
    if os.path.isfile(os.path.join(file_directory, "Sys.vm")):
        file_read = open(os.path.join(file_directory, "Sys.vm"), "r")
        machine_code = translate(machine_code, "Sys", file_read)

    # Process all others after
    for file in os.listdir(file_in):
        if file.endswith(".vm") and file != "Sys.vm":
            machine_code = translate(machine_code, file.strip(".vm"), file_read)

    with open(file_out, "w") as out:
        for line in machine_code:
            out.write("".join(line) + "\n")
