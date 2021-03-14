// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/04/Fill.asm

// Runs an infinite loop that listens to the keyboard input.
// When a key is pressed (any key), the program blackens the screen,
// i.e. writes "black" in every pixel;
// the screen should remain fully black as long as the key is pressed. 
// When no key is pressed, the program clears the screen, i.e. writes
// "white" in every pixel;
// the screen should remain fully clear as long as no key is pressed.

// Put your code here.

(START)
@SCREEN 
D=A
@R1
M=D // Store address of screen for looping around screen

@KBD
D=M
@FILL
D;JGT // If keyboard is greater than 1 a key is being pressed
@EMPTY
D;JEQ // If keyboard is 0 then nothing is being pressed

@INPUT
0;JMP // Keep checking

(FILL)
@R0 
M=-1 // Set R0 to -1 (16 true pixels)
@POP
0;JMP
// (FILL) //

(EMPTY)
@R0
M=0 // Set R0 to 0 (16 false pixels)
@POP
0;JMP
// (EMPTY) //

(POP) // Populate screen from R0
@R0
D=M // Get input pixels (either T or F)

@R1
A=M	// Current SCREEN pixel
M=D	// Populate pixels

@R1
D=M+1	// Go to next pixel

@KBD
D=A-D	// Store value for (KDB - current position of screen)

@R1
M=M+1	// Go to next pixel
A=M

@POP
D;JGT // Jump if still more screen to be populated
// (POP) //

@START // GOTO start
0;JMP