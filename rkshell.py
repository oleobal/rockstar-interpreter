import sys
import readline
import traceback

import rockstar as rk

def run_shell():
    """
    The main function for the shell. You can write rockstar code
    line by line. You can also examine the context and the variables.
    You can take a look at a specific variable by citing it.
    Catching exceptions should come soon enough.
    You can quit the shell by entering 'exit', or Ctrl+D. 
    You can use the arrows to navigate up to previous commands.
    Does not work across separate shell sessions.
    """
    context = {'variables' : {}}

    while True:
        
        # capture input
        try:
            raw_input = input('rk> ')
        except EOFError:
            print('')
            break
        user_input = raw_input.strip()

        # special instructions
        if user_input.lower() == 'exit':
            break

        if user_input.lower() == 'context':
            print(context)
            continue

        if user_input.lower() == 'vars':
            print(*context['variables'].items(), sep='\n')
            continue

        # check context naming
        named_var = context['variables'].get(user_input, None)
        if named_var is not None:
            print(named_var)
            continue

        # process line
        try:
            ans = rk.preProcessLine(user_input)
            if ans:
                ans = rk.processInstruction(rk.tokenize(ans), context)
        except Exception as e:
            traceback.print_exc()

if '__main__' == __name__:
    run_shell()