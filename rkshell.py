import sys
try:
    import readline
except:
    pass
import traceback

import rockstar as rk

def run_shell(displayAST=False):
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

        if not user_input:
            continue

        # load file
        if user_input[0] == '<':
            try:
                with open(user_input[1:].strip()) as file:
                    rk.processTextBlock(file.readline(), file, context, isTopLevelBlock=True)
            except FileNotFoundError as e:
                print(e)
            continue

        # special instructions
        if user_input.lower() == 'exit':
            break

        if user_input.lower() == 'ast':
            displayAST=True
			#TODO make use of it
			
        if user_input.lower() == 'context':
            print(context)
            continue

        # display vars
        if user_input.lower() == 'vars':
            if context['variables']:
                ff = '%-20s' * 3
                print(ff % ('NAME', 'TYPE', 'VALUE'))
                print(*list(map(lambda item : ff % (item[0], item[1]['type'], item[1]['value']), context['variables'].items())), sep='\n')
            continue

        # clear context
        if user_input.lower() == 'clear':
            context = {'variables' : {}}
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