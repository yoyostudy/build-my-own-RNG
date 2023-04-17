# CMPT789 Project
This the project for 2022Fall CMPT789.

Topic:
Simulate Linux RNG

Team members:
Hugh Song, Yoyo Wang, Keye Zhou

# Instruction on running the code:

0. pip3 install keyboard

1. sudo su

2. python3 Linux_RNG.py

3. Hint:   "Let us initialize input pool --------"
           
           "please stop if entropy counter > thread"
   
   Action: Continuesly typing every button except the ENTER button

4. Hint:   "Entropy Count is Enough, you can press ENTER to stop"
   
   Action: Type ENTER button

5. Remark: If raised ERROR immediately after running the code, please use different python version or operating system.

# Structures:

0. Global functions:
   
   0.1. state refresh function
   
   0.2. mixing function
   
   0.3. extraction function

1. Classes:
   
   1.1. noise collector
   
   1.2. input pool
   
   1.3. output pool
   
# Flow:

GOAL: 10-byte output

1. if ENTROPY COUNT of Output Pool > ENTROPY THREAD of Output Pool -> 2 | else -> 3

2. Linux_RNG().output() - FINISH output 10 random bytes

3. if ENTROPY COUNT of Input Pool > ENTROPY THREAD of Input Pool -> 4 | else -> 5

4. Transfer 80 bit entropy from Input Pool to Output Pool -> 1

5. Collect entropy from noise source -> 3
   
