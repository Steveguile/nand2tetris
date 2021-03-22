import sys 
import os 
import logging

push_pop_commands = {"push", "pop"}
arithmetic_commands = {"add", "sub", "neg", "eq", "gt", "lt", "and", "or", "not"}
branching_commands = {"label", "if-goto", "goto"}
function_commands = {"function", "call", "return"}
segments = {"local": "@LCL", "argument": "@ARG", "this": "@THIS", "that": "@THAT"}

comments_enabled = True

def checkIgnoreLine(line: str):
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
    elif line[0]=="/" or line[0]=="\n":
        ignoreLine = True

    return ignoreLine

def memoryTranslate(file_name: str, command: str, mem_seg: str, value: str):
    """ Determines how to handle a given memory operation command in hack assembly \n
    Args: \n
        file_name   :   Name of file currently being converted to hack. Used for static variables \n
        command     :   Stack operation, see push_pop_commands \n
        mem_seg     :   Memory segment command applies to, see segments dict \n
        value       :   Value applied to command and memory segment \n
    Returns: \n
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
    """ Determines how to handle arithmetic command in hack assembly \n
    Args: \n
        count   :   Incremental count to increment and apply to every {eq, gt, lt} \n
        command :   Type of arithmetic command, see arithmetic_commands \n
    Returns: \n
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
    """ Determines how to handle brancing command in hack assembly \n
    Args: \n
        command :   Type of branching command, see branching_commands \n
        label   :   Branch label to jump to / set position of \n
    Returns: \n
        Machine code array corresponding to input command 
    """

    line_array = []

    if command == "label":        
        line_array.extend([f"({label})"])
    elif command == "if-goto":
        line_array.extend(["@SP", "AM=M-1", "D=M", f"@{label}", "D;JNE"])
    elif command == "goto":
        line_array.extend([f"@{label}", "0;JMP"])

    return line_array

def func(command: str, name: str, number: str, file_name: str, call_count: int):
    """ Determines how to handle function command in hack assembly \n
    Args: \n
        command     :   Type of function command, see function_commands \n
        name        :   Name of the function \n
        number      :   Number of arguments/local variables \n
        file_name   :   Name of the file \n
        call_count  :   Count of times function has been called in this file
    Returns: \n
        Machine code array corresponding to input command 
    """

    line_array = []
    call_string = str(call_count)

    if command == "function":
        line_array.extend([f"({name})"])                                                        # Generate label
        for local_vars in range(int(number)):                                                   # For every local variable
            if comments_enabled:                                                                
                line_array.extend([f"// push local 0 for {name}"])
            line_array.extend(memoryTranslate("", "push", "constant", "0"))                     # Call push constant 0
    elif command == "call":
        func_name = name.split(".")[1]
        line_array.extend([f"@{file_name}.{func_name}$ret.{call_string}", "D=A", "@SP", "A=M", "M=D", "@SP", "M=M+1"])      # Push return address label
        line_array.extend(["@LCL", "D=M", "@SP", "A=M", "M=D", "@SP", "M=M+1"])                 # Push LCL
        line_array.extend(["@ARG", "D=M", "@SP", "A=M", "M=D", "@SP", "M=M+1"])                 # Push ARG
        line_array.extend(["@THIS", "D=M", "@SP", "A=M", "M=D", "@SP", "M=M+1"])                # Push THIS
        line_array.extend(["@THAT", "D=M", "@SP", "A=M", "M=D", "@SP", "M=M+1"])                # Push THAT
        line_array.extend([f"@{number}", "D=A", "@5", "D=D+A", "@SP", "D=M-D", "@ARG", "M=D"])  # ARG = SP-(nArgs + 5)
        line_array.extend(["@SP", "D=M", "@LCL", "M=D"])                                        # LCL = SP
        line_array.extend(branching("goto", name))                                              # goto functionname
        line_array.extend([f"({file_name}.{func_name}$ret.{call_string})"])                     # label for return address
    elif command == "return":
        line_array.extend(["@LCL", "D=M", "@endFrame", "M=D"])                                  # endFrame = LCL
        line_array.extend(["@5", "D=D-A", "A=D", "D=M", "@retAddr", "M=D"])                     # retAddr = (*endFrame - 5)
        line_array.extend(["@SP", "AM=M-1", "D=M", "@ARG", "A=M", "M=D"])                       # *ARG = pop() (get return value (SP-1) onto arg)
        line_array.extend(["@ARG", "D=M", "@SP", "M=D+1"])                                      # SP = ARG + 1
        line_array.extend(["@endFrame", "D=M", "@1", "D=D-A", "A=D", "D=M", "@THAT", "M=D"])    # THAT = (*endFrame - 1)
        line_array.extend(["@endFrame", "D=M", "@2", "D=D-A", "A=D", "D=M", "@THIS", "M=D"])    # THIS = (*endFrame - 2)
        line_array.extend(["@endFrame", "D=M", "@3", "D=D-A", "A=D", "D=M", "@ARG", "M=D"])     # ARG = (*endFrame - 3)
        line_array.extend(["@endFrame", "D=M", "@4", "D=D-A", "A=D", "D=M", "@LCL", "M=D"])     # LCL = (*endFrame - 4)
        line_array.extend(["@retAddr", "A=M", "0;JMP"])                                         # goto retAddr

    return line_array
    
def translate(machine_code: str, file_name: str, file_in: str):
    """ Determines what type of command each vm line contains and calls functions accordingly \n
    Args: \n
        machine_code (np array) :   Resultant hack commands from each line of file_in \n
        file_name (str)         :   Name of input file 
        file_in (str)           :   String of input vm file \n
    Returns: \n
        Machine code array based on input vm file
    """

    arith_count = 0 # Arithmetic counter
    call_count = 0

    for line in file_in:

        commentPos = line.find('/')
        line = line[0:commentPos].strip() # Remove comment and outer whitespace
        if checkIgnoreLine(line):
            continue

        if comments_enabled:
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
            # Save changings func args, just add empty array elems to return
            if line[0] == "return":
                line.extend(["", ""]) 
            if line[0] == "call":
                call_count = call_count + 1
            machine_code.extend(func(line[0], line[1], line[2], file_name, call_count))

    return machine_code

def bootstrap():
    line_array = []
    line_array.extend(["@256", "D=A", "@SP", "M=D", "@LCL", "MD=-1", "@ARG", "MD=D-1", "@THIS", "MD=D-1", "@THAT", "M=D-1"])
    return line_array

# This allows you to run the script through command line
if __name__ == "__main__":

    # Do OS pathing for submission
    file_in = os.path.basename(sys.argv[1])
    file_directory = os.path.dirname(sys.argv[1])
    
    # If no file choose directory as file name 
    if not file_in:
        file_in = os.path.basename(file_directory)

    if not file_directory:
        file_directory = file_in

    file_out = f"{os.path.join(file_directory, file_in.strip('.vm'))}.asm"

    machine_code = []

    sys_exists = os.path.isfile(os.path.join(file_directory, "Sys.vm"))   
        
    # Process Sys.init call first
    if sys_exists: 
        # Add bootstrap code
        machine_code.extend(bootstrap())
        # Call to Sys.init
        machine_code.extend(["// call Sys.init 0"])
        machine_code.extend(func("call", "Sys.init", "0", "Sys", 0))

    # Process all others after
    logging.warning("######START######")
    logging.warning(f"{sys.argv[1]}")
    logging.warning(f"{file_in}")
    logging.warning(f"{file_directory}")
    logging.warning("#######END#######")

    for file in os.listdir(file_directory):
        if file.endswith(".vm") and file != "Sys.vm":
            read = os.path.join(file_directory, file)
            if os.path.isfile(read):
                file_read = open(read, "r")
                machine_code = translate(machine_code, file.strip(".vm"), file_read)

    # Process function Sys.init
    if sys_exists:
        file_read = open(os.path.join(file_directory, "Sys.vm"), "r")
        machine_code = translate(machine_code, "Sys", file_read)

    with open(file_out, "w") as out:
        for line in machine_code:
            out.write("".join(line) + "\n")
            