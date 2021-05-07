import os 
import sys 
import logging
from JackTokenizer import JackTokenizer
from CompilationEngine import CompilationEngine

class JackAnalyzer:
    def __init__(self, in_arg):

        self.file = ""
        self.file_dir = ""

        # If file get file name and path, if not file then file_dir is in arg
        if (os.path.isfile(in_arg)):
            self.file = os.path.basename(in_arg)
            self.file_dir = os.path.dirname(in_arg)
        else: 
            self.file_dir = in_arg

    def processFiles(self):

        file_out = ""

        # If this is just a file then process once
        # Else process for each jack file
        if self.file:
            self.fileHandler(self.file)
        else:
            for file in os.listdir(self.file_dir):
                if file.endswith(".jack"):
                    self.fileHandler(file)

    def fileHandler(self, file):
        file_out = self.fileOutName(f"{file}_tokens")
        tokenizer = JackTokenizer(os.path.join(self.file_dir, file))
        token_array = tokenizer.token_array
        
        with open(file_out, "w") as out:
            for line in token_array:
                out.write("".join(line) + "\n")

        compilation_engine = CompilationEngine(file_out)
        compiled_xml = compilation_engine.compile_out

        file_out = self.fileOutName(f"{file}")
        with open(file_out, "w") as out:
            for line in compiled_xml:
                out.write("".join(line) + "\n")

    def fileOutName(self, file_name):
        return f"{os.path.join(self.file_dir, file_name.strip('.jack'))}.xml"


if __name__ == "__main__":

    # Do OS pathing for submission
    if len(sys.argv) > 1:
        jackAnalyzer = JackAnalyzer(sys.argv[1])
        jackAnalyzer.processFiles()
    


