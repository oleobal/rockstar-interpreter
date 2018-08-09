import sys
import re
import argparse
import pdb
import pprint as prettyprint

from rkop import *
import rkshell

VERBOSE = 0

def pprint(o):
	print()
	prettyprint.pprint(o)
	print()


def LOG(*args, sep=' '):
	if VERBOSE:
		if len(args) == 1:
			pprint(args[0])
		else:
			print(*args, sep=sep)


class InputProgramError(Exception):
	pass


def raiseError(line, text):
	raise InputProgramError("Line : "+str(line)+"\nError : "+str(text))


def parseConditionalExpression(line, i):

	# 1. capture first variable
	var1, ind = getNextVariable(line, i)
	if var1 == None:
		raiseError(line, "Invalid flow control")

	i = ind + 1

	# 2. identify operator
	# notes :
	# - always begins by is + optional negation
	# then either 'as X as' or 'X than'
	tokens = []
	words = line[i:].split()
	LOG('words:', words)
	is_nature = []
	it = 0
	while it < len(words):

		nextWord = words[it].lower()

		if nextWord in ['is', 'are', 'were']:
			is_nature.append('is')
			LOG('IS')
		
		elif nextWord in ['aint', 'wasnt', 'werent']:
			is_nature.extend(['is', 'not'])
			LOG('IS NOT')

		elif nextWord in ['not', 'no']:
			is_nature.append('not')
			LOG('NOT')

		# as X as
		elif nextWord == 'as':
			
			if it + 2 >= len(words):
				raiseError(line, 'Invalid conditional expression')
			
			name = ' '.join([nextWord, *words[it+1:it+3]])

			op = CONDITIONAL_OPS.get(name, None)

			if not op:
				raiseError(name, 'Invalid conditional operator')
			
			LOG('identified conditional op :', op, 'from', line, 'at', it)
			
			tokens.append({'type' :TokenType.CONDITIONAL_OP, 'value' : op})
			
			it += 3

			# found operator, we can bail out
			break

		# X than
		else:
			# search for 'than' word next to current word
			if it + 1 >= len(words) or words[it + 1] != 'than':
				break

			name = nextWord + ' ' + words[it + 1]

			op = CONDITIONAL_OPS.get(name, None)

			if not op:
				raiseError(name, 'Invalid conditional operator')
			
			LOG('identified conditional op :', op, 'from', line, 'at', it)
			
			tokens.append({'type' :TokenType.CONDITIONAL_OP, 'value' : op})

			it += 2

			# found operator, we can bail out
			break
		
		it += 1

	if not tokens and is_nature:
		# figure out op of 'not is'
		# is -> EQ
		# is not -> NE
		# is not not -> EQ
		notnot = sum([1 for t in is_nature if t == 'not'])
		tokens.append({'type' : TokenType.CONDITIONAL_OP, 'value' : 'EQ' if not notnot%2 else 'NE'})

	elif tokens and is_nature:
		# see you later
		# utimately : 'A is not as X as B'
		# but this requires 'unary' negation operator
		# once you can evaluate properly, you can merge this 'if' with the one above
		# with 'if is_nature' only
		pass

	elif not tokens and not is_nature:
		raiseError(line, 'Invalid boolean expression : no conditions')

	# move cursor to right position in original line
	i += sum([len(words[w]) + 1 for w in range(it)])
	
	LOG(i, line[i:])

	# 3. capture second variable
	var2, ind = getNextVariable(line, i)
	if var2:
		tokens.append(var2)
		i += ind + 1	
	else:
		tokens += [{"type":"expression", "value":tokenize(line[i:])}]
	return [var1] + tokens, i


def preProcessLine(line):
	"""
	Formatting to be done line per line, purely on text
	"""
	# removing comments
	line = re.sub(r"\(.*\)", "", line)
	# removing single quotes
	line = re.sub(r"'s\W+", " is ", line)
	line.replace("'", "")
	# removing non alphabetical characters (save for . , " and numbers)
	line = re.sub(r"[^a-zA-Z0-9.,\" ]+", "", line)
	# FIXME this is actually wrong because we'll also be removing them from string literals
	# and it's not as simple as avoiding what is inside "", because of poetic string literals
	# and also poetic things can contain keywords
	# so basically we have to parse just to remove unwanted characters
	# aint that great
	
	# TODO fold multiple consecutive spaces into a single one ?
	
	# removing whitespace
	line = line.strip()
	
	return line


def getNextWord(text, index):
	"""
	Utility function
	Given a string and a position in that string
	returns the word (delimited by whitespace) that follows
	"""
	
	if index == len(text):
		return None
		# FIXME
	
	text = text[index:]
	result = ""
	i = 0
	while i < len(text):
		if text[i].strip() != "" :
			result+= text[i]
			i+=1
		else:
			break
	
	return result

def getNextVariable(line, index):
	"""
	Utility function
	If there is a variable at <index> in <line>, it returns it (in dict form),
	along with the new index. Else, it returns None and the same index
	"""
	nextWord = getNextWord(line, index)
	if nextWord == None:
		return None, index
	
	# common variables
	if nextWord.lower() in ("a", "an", "the", "my", "your") :
		varName = nextWord.lower()+" "
		index+=len(nextWord)+1
		nextWord = getNextWord(line,index)
		if nextWord.lower() != nextWord :
			raiseError(line, "Invalid common variable name")
		varName += nextWord
		index+=len(nextWord)
		return ({"type":"variable", "value":varName}, index)
		
	# TODO proper variables
	elif nextWord[0] != nextWord[0].lower():
		varName = ""
		while index < len(line) and nextWord[0] != nextWord[0].lower():
			varName += nextWord+" "
			index+=len(nextWord)+1
			nextWord = getNextWord(line,index)
		varName=varName[:-1] ; index-=1 # remove last space
		return({"type": "variable", "value":varName},index)
	
	return None, index
	

def tokenize(preProcessedLine):
	"""
	Separates a line into a token tree
	Context-unaware
	"""
	line = preProcessedLine
	tokenTree = []
	
	i = -1
	while i < len(line) :
		i+=1
		newToken = {"type":"none", "value":None}
		nextWord = getNextWord(line, i)
		if nextWord == None:
			break
		# my suspicion is that it is the sign of a  bigger problem, but oh well
		
		# separator
		try:
			if line[i] == " ":
				continue
		except IndexError :
			break
			
		# string literal
		if line[i] == "\"" :
			i+=1
			newToken["type"] = "string"
			newToken["value"] = ""
			while line[i] != "\"":
				newToken["value"]+=line[i]
				i+=1
			tokenTree.append(newToken)
			continue

		# numeric literal
		if line[i] in ("0","1","2","3","4","5","6","7","8","9") :
			# this is actually not conform to the spec, which says all numbers should be DEC64
			# not like anyone will ever care enough
			try:
				newNum = float(nextWord)
			except ValueError:
				raiseError(preProcessedLine, "Invalid numeric literal : "+str(newToken))
			tokenTree.append({"type":"number","value":newNum})
			i+=len(nextWord)
			continue
	
		# boolean literal
		if nextWord in ("true", "right", "yes", "ok") :
			tokenTree.append({"type":"boolean", "value":True})
			i+=len(nextWord)
			continue
		if nextWord in ("false", "wrong", "no", "lies") : # what, no 'nope' ? 
			tokenTree.append({"type":"boolean", "value":False})
			i+=len(nextWord)
			continue
		
		# operations

		if nextWord in ("Say", "Shout", "Whisper", "Scream"):
			tokenTree.append({"type":"operator", "value":"say"})
			i+=len(nextWord)
			continue

		# A simple print statement w/o new line
		if nextWord in ("Spit", 'Stutter'):
			tokenTree.append({'type': 'operator', 'value': 'stutter'})
			i += len(nextWord)
			continue
		
		# flow control
		global FLOW_CONTROL_OPS
		if nextWord in FLOW_CONTROL_OPS :
			tokenTree.append({"type":"flow control", "value":nextWord})
			i+=len(nextWord)+1

			expr_tokens, i = parseConditionalExpression(line, i)
			tokenTree.extend(expr_tokens)
			
			i=len(line)
			continue
		
		# loop control
		# TODO errors if misused, but honestly whatev
		if line[i:].find("Break it down") == 0 or nextWord == "break" :
			tokenTree.append({"type":"loop control", "value":"break"})
			i=len(line)
			continue
		if line[i:].find("Take it to the top") == 0 or nextWord == "continue" :	
			tokenTree.append({"type":"loop control", "value":"continue"})
			i=len(line)
			continue
		
		# function declaration
		if nextWord == "takes" :
			if tokenTree[-1]["type"] != "variable" :
				raiseError(line, "Incorrect function declaration") # TODO should be more rigorous
			tokenTree[-1]["type"] = "function"
			tokenTree.append({"type":"function declaration", "value":"function declaration"})
			i+=len(nextWord)+1
			arguments = line[i:].split(" and ")
			# could also be made part of previous token
			tokenTree.append({"type":"function argument list","value":arguments})
			i = len(line)
			continue
		
		# function call
		if nextWord == "taking" :
			# appends a token "function call"
			# it has a list 
			if tokenTree[-1]["type"] != "variable" :
				raiseError(line, "Incorrect function declaration") # TODO should be more rigorous
			tokenTree[-1]["type"] = "function"
			funcTok = tokenTree.pop()
			
			i+=7
			# FIXME for now functions only take variables and literals
			# because there's no clear guideline on where boundaries expression
			# are; that is to say, how to distinguish between :
			# > (Multiply taking my heart, my love) is nothing
			# and
			# > Multiply taking my heart, (my love is nothing)
			# ?
			# Both are valid expressions.. Rockstar has no mean of indicating
			# priority, apparently by design.
			restOfLine = line[i:].split(",")
			# We separate on "," and trim whitespace afterwards, but that's
			# just our interpretation of the spec
			arguments = []
			for l in restOfLine :
				
				a = tokenize(l.strip())
				arguments.append(a[0])
				if len(a)>1:
					# FIXME bullshit method
					if a["type"] == "variable":
						i+=len(getNextVariable(line,i)[0]["value"])+1
					elif a["type"] == "number":
						i+=len(getNextWord(line,i))+1
					elif a["type"] == "string":
						i=line[i+1:].find("\"")
					break
				else:
					i+=len(l)+1
			
			tokenTree.append({"type":"function call", "value":(funcTok, {"type":"function call argument list", "value":arguments})})
			
			continue
		
		
		# function return
		if line[i:9] == "Give back" :
			tokenTree.append({"type":"function return", "value":"function return"})
			i+=10
			tokenTree.append({"type":"expression", "value":tokenize(line[i:])})
			i = len(line)
			continue
		
		# assignment
		if nextWord == "Put" :
			tokenTree.append({"type":"operator", "value":"assignment put"})
			i+=4
			assignEndIndex = line.find("into")
			if assignEndIndex == -1 :
				raiseError(line, "Put without a corresponding into")
			tokenTree.append({"type":"expression", "value":tokenize(line[i:assignEndIndex])}) # sub expression
			tokenTree.append({"type":"operator", "value":"assignment into"})
			i=assignEndIndex+4
			continue

		# arithmetic operators
		if nextWord in ARITHMETIC_OPS:
			tokenTree.append({"type" : TokenType.ARITHMETIC_OP, "value" : ARITHMETIC_OPS[nextWord]})
			i += len(nextWord)
			continue

		# poetic assignment
		
		# in this shitty language, is can either be initialisation or comparison
		if nextWord in ("is", "was", "were") :
			if tokenTree[-1]["type"] == "variable" :
				tokenTree.append({"type":"operator", "value":"poetic assignment"})
				i+=len(nextWord)+1
				nextWord = getNextWord(line,i)
				# poetic type literal
				if nextWord in ("true", "right", "yes", "ok"):
					tokenTree.append({"type":"boolean", "value":True})
				elif nextWord in ("false", "wrong", "no", "lies"):
					tokenTree.append({"type":"boolean", "value":False})
				elif nextWord in ("null", "nobody", "nowhere", "empty", "gone") :
					tokenTree.append({"type":"null", "value":None})
				else:
					# poetic number literal
					numVal = ""
					while i<len(line):
						if "." in nextWord :
							z = nextWord.split(".")
							numVal+=str(len(z[0])%10)
							numVal+="."
							numVal+=str(len(z[1])%10)
						else :
							numVal+=str(len(nextWord)%10)
						i+=len(nextWord)+1
						nextWord = getNextWord(line,i)
					
					try:
						num = int(numVal)
					except ValueError:
						pass
					try:
						num = float(numVal)
					except ValueError :
						raiseError(line, "Invalid poetic literal")
					tokenTree.append({"type":"number", "value":num})
					i+=len(nextWord)
					continue
					
		if nextWord == "says" :
			if tokenTree[-1]["type"] == "variable" :
				tokenTree.append({"type":"operator", "value":"poetic assignment"})
				i+=len(nextWord)+1
				tokenTree.append({"type":"string", "value":line[i:]})
				i=len(line)
			else:
				raiseError(line, "Invalid poetic string assignment")
			
		# treat all keywords before variables so they're the only thing left
		
		# common variable
		var, ind = getNextVariable(line, i)
		if var != None:
			tokenTree.append(var)
			i=ind
		
		# pronouns
		# Making fun of SJWs is fun, right ? right ? right ? Should I put more
		# inclusive pronouns in guys ? SJWs are so dumb right ?
		# Actually, fuck the spec. Fuck these jokes. Fuck people who think
		# humour is just references marking your belonging to a group.
		# Fuck pervasive conservatism. Fuck militant apathy. Fuck Dylan Beattie.
		# If you want your program that uses those to compile, edit this.
		if nextWord.lower() in ("it", "he", "she", "him", "her", "they", "them"):
			tokenTree.append({"type":"pronoun", "value":"doesn't matter"})
			i+=len(nextWord)
			continue
		
	return tokenTree


def guessTypeOf(thing):
	"""
	Guess what the type of the thing (variable) is
	"""
	return "mysterious"
	# TODO


def evaluate(expression, context):
	# FIXME maybe evaluate should return an expression instead ? Not sure
	"""
	returns a tuple: 
	 (what an expression evaluates to, its type)
	types : "mysterious" (undefined), "null", "boolean", "number", "string", "object"
	
	:param expression: a tokenized tree (from tokenize())
	:param context:
	"""

	LOG('before', expression)

	rexpr = None
	
	if type(expression) is str :
		rexpr =  (expression, "string")
	elif type(expression) is int or type(expression) is float : #FIXME many others
		rexpr =  (expression, "number")
	
	elif type(expression) is tuple :
		rexpr = expression
	
	elif type(expression) is list:
		resultingExpr = []
		for item in expression :
			resultingExpr.append(evaluate(item, context))
		
		# for now just special case
		
		if len(resultingExpr) == 1:
			rexpr = resultingExpr[0]
					
		# arithmetic
		
		# Right associative operators
		elif resultingExpr[1]["type"] == TokenType.ARITHMETIC_OP:
			# assuming it's a binary operator
			left = resultingExpr[0]
			right = evaluate(resultingExpr[2:],context)
			rexpr = (arithmetic_operations[resultingExpr[1]['value']](left[0], right[0]), left[1])	
	
	elif expression["type"] == "expression" :
		rexpr = evaluate(expression["value"], context)
	
	elif expression["type"] == "function call" :
		return executeFunction(expression["value"][0]["value"], expression["value"][1]["value"], context)
	
	else:
		# Literals
		if expression["type"] in ("string", "number", "boolean")  :
			rexpr = (expression["value"], expression["type"])
		
		if expression["type"] == "variable" :
			rexpr = (context["variables"][expression["value"]]["value"], context["variables"][expression["value"]]["type"])
			context["last named variable"] = expression["value"]
			
		if expression["type"] == "pronoun" :
			if context["last named variable"] == None:
				raiseError(expression, "Pronoun referring to nothing")
			else :
				var = context["variables"][context["last named variable"]]
				rexpr = (var["value"], var["type"])

	LOG('after:', rexpr)
	if rexpr is not None:
		return rexpr
	
	return expression


def checkDefinitionValidity(name, type, context):
	"""
	Checks that it is valid to define something with this name and type
	Will throw an exception if it's not quite right
	:param name: the name of the new thing
	:param type: its type ("variable" or "function")
	:param context: the context to loop up
	"""
	# this is outside spec.. but sensible.
	if type == "variable":
		if name in context["functions"]:
			raiseError(name, "Variable name already attributed to function")
	if type == "function":
		if name in context["variables"]:
			raiseError(name,"Function name already attributed to variable")
	
	
def processConditionalExpression(comparisonExpression, context):
	"""
	Takes in a comparison and returns True or False
	:param comparisonExpression: of the form {variable, comparison operator, {sub expression to evaluate}}
	"""
	comped = context["variables"][comparisonExpression[0]["value"]]["value"]
	op = comparisonExpression[1]["value"]
	comptarget = evaluate(comparisonExpression[2], context)[0]
	# reminder evaluate returns (value, 'type'), maybe wasn't such a good idea
	
	if op not in conditional_operations:
		raiseError('{} : unknown conditional operator'.format(op))
	# admitedly only binary
	return conditional_operations[op](comped, comptarget)

	return False


def executeFunction(name, arguments, context):
	"""
	Creates a new context, and executes the given function with that new context
	
	:param name: function name
	:param arguments: list of arguments
	:param context: the context to which the new function will be attached
	:returns: the function return value, or None
	"""
	
	# build new context
	newContext = getNewContext(name, context)
	
	function = context["functions"][name]
	funcArgNames = function[2]["value"]
	
	newContextName = name+"("
	a = 0
	for a in range(len(arguments)):
		newContext["variables"][funcArgNames[a]] = {}
		
		newContext["variables"][funcArgNames[a]]["value"], newContext["variables"][funcArgNames[a]]["type"] = evaluate(arguments[a], context)
		
		newContextName+=funcArgNames[a] + str(newContext["variables"][funcArgNames[a]])+","
	newContext["name"] = newContextName[:-1] + ")"
	
	newContext["functions"] = context["functions"]
	
	
	# execute function
	instructionList = function[3]["value"]
	for i in instructionList:
		if i[0]["type"] == "function return" :
			if len(i) == 1:
				return None
			else:
				return evaluate(i[1:], newContext)
		else:
			processInstruction(i, newContext)
	
	return None

def processLoop(block, context):
	"""
	Processes loops, either as "block" expressions or as lists of instructions
	Contains logic for processing return values (breaks/continues)
	When one of the instructions in the block returns a command, execution
	stops there and that value is returned.
	
	:param block: either a block expression or a list of instruction
	:param context: the context
	:param returns: None, or a string containing a command if it needs to
	"""
	
	if type(block) is dict:
		if block["type"] == "block" :
			instructionList = block["value"]
	elif type(block) is list:
		instructionList = block
	else:
		print(type(block))
	
	for i in instructionList:
		r = processInstruction(i,context)
		if r in ("break", "continue"):
			break
	
	return r


def processInstruction(instruction, context):
	"""
	Execute instruction
	:param instruction: a tokenized tree, or a block expression
	:param context: the context
	:returns: None, or a string containing a command if it needs to
	  change code execution (for breaks and continues)
	"""

	LOG(instruction)
	
	if type(instruction) is dict:
		if instruction["type"] == "block" :
			return processBlock(instruction, context)
	
	# I/O
	if instruction[0]["value"] == "say" :
		print(str(evaluate(instruction[1:], context)[0]))

	# Print without a new line
	if instruction[0]['value'] == 'stutter':
		print(str(evaluate(instruction[1:], context)[0]), end=' ')

	# function declaration
	if len(instruction) >= 3 and instruction[1]["type"] == "function declaration":
		# let's allow redefinition
		# TODO add a warning once we have something that allows warnings
		checkDefinitionValidity(instruction[0]["value"],"function",context)
		context["functions"][instruction[0]["value"]] = instruction
	
	# Variable assignment
	if instruction[0]["value"] == "assignment put" :
		# it should go instruction : (0) put (1) expression (2) into (3) variable
		v, t = evaluate(instruction[1], context)
		checkDefinitionValidity(v,"variable",context)
		context["variables"][instruction[3]["value"]] = {"value" : v, "type" : t}	
		context["last named variable"] = instruction[3]["value"]
		LOG('CONTEXT:', context)
	# TODO
	
	# Poetic assignment
	if instruction[0]["type"] == "variable" and instruction[1]["value"] == "poetic assignment" :
		checkDefinitionValidity(instruction[0]["value"],"variable",context)
		context["variables"][instruction[0]["value"]] = {"type" : instruction[2]["type"], "value":instruction[2]["value"]}
		context["last named variable"] = instruction[0]["value"]
		# already handled in the tokenizer
	
	# Conditionals
	if instruction[0]["value"] == "If" :
		if processConditionalExpression(instruction[1:4], context) :
			return processLoop(instruction[4], context)
	# TODO else
	
	
	if instruction[0]["value"] == "While" :
		while processConditionalExpression(instruction[1:4], context) :
			r = processLoop(instruction[4], context)
			if r == "break":
				break
			if r == "continue":
				continue
				
	if instruction[0]["value"] == "Until" :
		while not processConditionalExpression(instruction[1:4]) :
			r = processLoop(instruction[4],context)
			if r == "break":
				break
			if r == "continue":
				continue
	
	# loop control
	
	# spec is not clear on what exactly breaks/continues do
	# "as in block based languages", no shit, there's probably a language
	# where a robo-leg kicks your ass when breaking or something
	# so let's do as in python
	
	if instruction[0]["type"] == "loop control" :
		return instruction[0]["value"]
	
	return None
	

def getNewContext(name, super):
	"""
	Utility function that returns a neat new context
	:param name: its name
	:param super: the parent context
	"""
	context = {}
	context["variables"] = {}
	context["last named variable"] = None
	context["functions"] = {}
	# for call stack
	context["name"] = name
	context["super"] = super 
	
	return context

def processTextBlock(line, iterator, context):
	"""
	This works like processProgram, but instead of executing each instruction
	as they are finished, they are appended to a list that is returned once
	an empty line encountered (a block-starting keyword triggers a recursive
	call to this function)
	
	Here is an instance of return value :
	(with added comments)
	[
	 # list of tokens = instruction
	 {'type': 'flow control', 'value': 'If'},
	 
	 # expression evaluated for 'If' follows
	 # as <expression> <comparator> <expression>
	 # FIXME : or is it just variable in first place ? Should be expression
	 {'type': 'variable', 'value': 'my heart'},
	 {'type': 'comparator', 'value': 'EQ'},
	 {'type': 'expression',
	  'value': [{'type': 'number', 'value': 400.0}]},
	  
	 # block to be executed follows
	 {'type': 'block',
	  'value':
	   [
	    # list of instructions follows
		[{'type': 'operator', 'value': 'say'},
             {'type': 'variable', 'value': 'my heart'}],
	    [{'type': 'loop control', 'value': 'break'}]
	   ]
	 }
	]
	
	:param line: first line of the block
	:param iterator: the line iterator over the input code
	:param context: the program context
	:returns: a list of instructions, each as a list itself
	"""

	instruction = []
	
	while preProcessLine(line) != "" :
		line = preProcessLine(line)
		
		currentLine = tokenize(line)
		
		instruction.append(currentLine)
		
		# sub block
		global FLOW_CONTROL_OPS
		if currentLine[0]["value"] in FLOW_CONTROL_OPS :
			line = next(iterator, "")
			currentLine.append({"type":"block", "value":processTextBlock(line, iterator, context)})
		
		line = next(iterator, "")
	
	
	return instruction


def processProgram(line, iterator, context, displayAST=False):
	"""
	This reads lines from whatever wrapper it has been given and executes
	each instruction it finds.
	
	Recursion is complicated, I split this from processTextBlock for my
	brain's sake.
	
	:param line: first line of the program
	:param iterator: the line iterator over the input code
	:param displayAST: (optional, False) display the AST before execution
	"""
	# discard leading empty lines
	# I had this problem while processing text
	while not line.strip():
		line = next(iterator, "")
	


	while line != "":
		line = preProcessLine(line)
		
		if line == "" :
			line = next(iterator, "")
			continue
		
		instruction = tokenize(line)
		
		# blocks
		global FLOW_CONTROL_OPS
		# let us assume functions can only be declared at top level
		if instruction[0]["value"] in FLOW_CONTROL_OPS or instruction[1]["type"] == "function declaration":
			line = next(iterator, "")
			instruction.append({"type":"block", "value":processTextBlock(line, iterator, context)})
		
		if displayAST:
			pprint(instruction)
		
		processInstruction(instruction,context)
		
		line = next(iterator, "")
	

if __name__ == '__main__':

	argparser = argparse.ArgumentParser(description="Interpreter for the Rockstar programming language.")
	argparser.add_argument('filepath', nargs='?', help='path to the file to interpret')
	argparser.add_argument('-v', '--verbose', action='store_true', help='show detailed debug messages')
	argparser.add_argument('-t', '--displayAST', action='store_true', help='Display the AST before executing each instruction.', default=False)
	
	args = argparser.parse_args()
	
	VERBOSE = args.verbose

	context = getNewContext("Main", None)
	
	if args.filepath:
		# reading input file from argument
		with open(args.filepath) as f:
			processProgram(f.readline(), f, context, displayAST=args.displayAST)

	else:
		# fire up the rockstar shell
		rkshell.run_shell(displayAST=args.displayAST)
