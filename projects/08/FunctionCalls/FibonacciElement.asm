// function Sys.init 0
(Sys.init)
// push constant 4
@4
D=A
@SP
A=M
M=D
@SP
M=M+1
// call Main.fibonacci 1
@RETURN.Main.fibonacci
@LCLD=M
@SP
A=M
M=D
@SP
M=M+1
@ARGD=M
@SP
A=M
M=D
@SP
M=M+1
@THISD=M
@SP
A=M
M=D
@SP
M=M+1
@THATD=M
@SP
A=M
M=D
@SP
M=M+1
@1
D=A
@5
D=D+A
@SP
D=M-D
@ARG
M=D
@SP
D=M
@LCL
M=D
D=0
@Main.fibonacci
D;JEQ
(RETURN.Main.fibonacci)
// label WHILE
(WHILE)
// goto WHILE
D=0
@WHILE
D;JEQ
