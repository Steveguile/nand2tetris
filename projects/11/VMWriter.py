
class VMWriter():
    def __init__(self, file_name: str):
        self.file = open(file_name, "w")

    def writePush(self, segment: str, index: [int, str]):
        if segment == "field":
            segment = "this"
        self.file.write(f"push {segment} {index}\n")

    def writePop(self, segment: str, index: int):
        if segment == "field":
            segment = "this"
        self.file.write(f"pop {segment} {index}\n")

    def writeArithmetic(self, command: str):
        if command == "*":
            self.file.write("call Math.multiply 2\n")
        elif command == "/":
            self.file.write("call Math.divide 2\n")
        elif command == "+":
            self.file.write("add\n")
        elif command == "-":
            self.file.write("sub\n")
        elif command == "&":
            self.file.write("and\n")
        elif command == "|":
            self.file.write("or\n")
        elif command == "~":
            self.file.write("not\n")
        elif command == "<":
            self.file.write("lt\n")
        elif command == ">":
            self.file.write("gt\n")
        elif command == "=":
            self.file.write("eq\n")
        else:
            self.file.write(f"{command}\n") # Cases where using the word in constant string

    def writeLabel(self, label: str):
        self.file.write(f"label {label}\n")

    def writeGoto(self, label: str):
        self.file.write(f"goto {label}\n")

    def writeIf(self, label: str):
        self.file.write(f"if-goto {label}\n")

    def writeCall(self, name: str, n_args: int):
        self.file.write(f"call {name} {n_args}\n")

    def writeFunction(self, name: str, n_locals: int):
        self.file.write(f"function {name} {n_locals}\n")

    def writeReturn(self):
        self.file.write("return\n")

    def close(self):
        self.file.close()