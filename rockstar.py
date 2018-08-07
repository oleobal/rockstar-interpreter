import sys
import re
import argparse
import pdb
import pprint as prettyprint

def pprint(o):
	prettyprint.pprint(o)
	print()

from rkop import *
import rkshell

VERBOSE = 0

def LOG(*args, sep=' '):
	if VERBOSE:
		print(*args, sep=sep)
	#open('log.log', 'a+').write(sep.join(map(str, args)) + '\n')

class InputProgramError(Exception):
	pass

def raiseError(line, text):
	raise InputProgramError("Line : "+str(line)+"\nError : "+str(text))

def parseBooleanExpression(line, i):

	# 2. recognize operator
	# 2.5. recognize negation

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
			is_nature.append('is not')
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
			
			LOG('identified boolean op :', op, 'from', line, 'at', it)
			
			tokens.append({'type' :TokenType.BOOLEAN_OP, 'value' : op})
			
			it += 3

			# found operator, we can bail out
			break

		# X than
		else:
			# look back
			if it + 1 >= len(words) or words[it + 1] != 'than':
				break

			name = nextWord + ' ' + words[it + 1]

			op = CONDITIONAL_OPS.get(name, None)

			if not op:
				raiseError(name, 'Invalid conditional operator')
			
			LOG('identified boolean op :', op, 'from', line, 'at', it)
			
			tokens.append({'type' :TokenType.BOOLEAN_OP, 'value' : op})

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
		tokens.append({'type' : TokenType.BOOLEAN_OP, 'value' : 'EQ' if not notnot%2 else 'NE'})

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
	LOG(i)

	LOG('x', line[i], 'x')

	# 3. capture second variable
	var2, ind = getNextVariable(line, i)
	# if var2 == None:
	# 	raiseError(line, "Invalid flow control")
	if var2:
		tokens.append(var2)

	i += ind + 1	

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
	# removing non alphabetical characters (save for . " and numbers)
	# line = re.sub(r"[^a-zA-Z0-9.\" ]+", "", line)
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
	If there is a variable at <index> in <line>, it returns it (in dict form), along with the new index
	else, it returns None and the same index
	"""
	nextWord = getNextWord(line, index)
	
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
			newToken["type"] = "number"
			newToken["value"] = ""

			while i < len(line) and line[i]:
				newToken["value"]+=line[i]
				i+=1
			# this is actually not conform to the spec, which says all numbers should be DEC64
			# not like anyone will ever care enough
			try :
				newToken["value"] = int(newToken["value"])
			except ValueError:
				pass
			try:
				newToken["value"] = float(newToken["value"])
			except ValueError:
				raiseError(preProcessedLine, "Invalid numeric literal")
			tokenTree.append(newToken)
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

			expr_tokens, i = parseBooleanExpression(line, i)
			tokenTree.extend(expr_tokens)
	
			# var, ind = getNextVariable(line, i)
			# if var == None:
			# 	raiseError(line, "Invalid flow control")
			# tokenTree.append(var)
			# i=ind+1

			# nextWord = getNextWord(line, i)
			
			# # comparison is
			# if nextWord == "is" :
			# 	i+=3
			# 	nextWord = getNextWord(line,i)
			# 	if nextWord == "not" :
			# 		tokenTree.append({"type":"comparator","value":"NE"})
			# 		i+=4
			# 		nextWord = getNextWord(line,i)
			# 	else :
			# 		tokenTree.append({"type":"comparator","value":"EQ"})
			# elif nextWord == "aint" :
			# 	tokenTree.append({"type":"comparator","value":"NE"})
			# 	i+=5
			# 	nextWord = getNextWord(line,i)
			
			# tokenTree.append({"type":"expression", "value":tokenize(line[i:])})
			# i=len(line)
			
			# TODO other comparisons
			
			continue
		
		# loop control
		# TODO errors if misused, but honestly whatev
		
		if line[i:].find("Break it down") == 0 or nextWord == "break" :
			tokenTree.append({"type":"loop control", "value":"break"})
			i=len(line)
		if line[i:].find("Take it to the top") == 0 or nextWord == "continue" :	
			tokenTree.append({"type":"loop control", "value":"continue"})
			i=len(line)
		
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
		
		# TODO treat all keywords before variables so the only thing left is variables
		
		# common variable
		
		
		
		var, ind = getNextVariable(line, i)
		if var != None:
			tokenTree.append(var)
			i=ind
		
		
		
		# pronouns
		# Making fun of SJWs is fun, right ? right ? right ? Should I put more inclusive pronouns in guys ? SJWs are so dumb right ?
		# Actually, fuck the spec. Fuck these jokes. Fuck people who think humour is just references marking your
		# belonging to a group. Fuck pervasive conservatism. Fuck militant apathy. Fuck Dylan Beattie.
		# If you want your program that uses those to compile, then edit this yourself.
		#if nextWord.lower() in ("it", "he", "she", "him", "her", "they", "them", "ze", "hir", "zie", "zir", "xe", "xem", "ve", "ver"):
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
	
	if type(expression) is tuple :
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
	

	# TODO arithmetic, recursive expressions, etc
	#elif expression['type'] == TokenType.ARITHMETIC_OP: # +plus, *times, -minus, /over
	#	pass
	
	
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


def doIt(comparisonExpression):
	"""
	Takes in a comparison and returns True or False
	:param comparisonExpression: of the form {variable, comparison operator, {sub expression to evaluate}}
	"""
	comped = context["variables"][comparisonExpression[0]["value"]]["value"]
	op = comparisonExpression[1]["value"]
	comptarget = evaluate(comparisonExpression[2], context)[0]
	# reminder evaluate returns (value, 'type'), maybe wasn't such a good idea
	if op == "EQ":
		if comped == comptarget :
			return True
	elif op == "NE":
		if comped != comptarget :
			return True
	return False

	
def processBlock(block, context):
	"""
	Processes blocks, either as "block" expressions or as lists of instructions
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

	if instruction[0]['value'] == 'stutter':
		print(str(evaluate(instruction[1:], context)[0]), end=' ')

	
	# Variable assignment
	
	if instruction[0]["value"] == "assignment put" :
		# it should go instruction : (0) put (1) expression (2) into (3) variable
		v, t = evaluate(instruction[1], context)
		context["variables"][instruction[3]["value"]] = {"value" : v, "type" : t}	
		context["last named variable"] = instruction[3]["value"]
		LOG('CONTEXT:', context)
	# TODO
	
	# Poetic assignment
	if instruction[0]["type"] == "variable" and instruction[1]["value"] == "poetic assignment" :
		context["variables"][instruction[0]["value"]] = {"type" : instruction[2]["type"], "value":instruction[2]["value"]}
		context["last named variable"] = instruction[0]["value"]
		# already handled in the tokenizer
	
	# Conditionals
	if instruction[0]["value"] == "If" :
		if doIt(instruction[1:4]) :
			return processBlock(instruction[4], context)
	# TODO else
	
	
	if instruction[0]["value"] == "While" :
		while doIt(instruction[1:4]) :
			r = processBlock(instruction[4], context)
			if r == "break":
				break
			if r == "continue":
				continue
			
				
	if instruction[0]["value"] == "Until" :
		while not doIt(instruction[1:4]) :
			r = processBlock(instruction[4],context)
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
		if currentLine[0]["value"] in FLOW_CONTROL_OPS:
			line = next(iterator, "")
			currentLine.append({"type":"block", "value":processTextBlock(line, iterator, context)})
			
		line = next(iterator, "")
	
	
	return instruction


def processProgram(line, iterator, context):
	"""
	This reads lines from whatever wrapper it has been given and executes
	each instruction it finds.
	
	Recursion is complicated, I split this from processTextBlock for my
	brain's sake.
	
	:param line: first line of the program
	:param iterator: the line iterator over the input code
	:param context: the program context
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
		if instruction[0]["value"] in FLOW_CONTROL_OPS:
			line = next(iterator, "")
			instruction.append({"type":"block", "value":processTextBlock(line, iterator, context)})
		
		processInstruction(instruction,context)
		
		line = next(iterator, "")
	
	

if __name__ == '__main__':

	argparser = argparse.ArgumentParser()
	argparser.add_argument('filepath', nargs='?', help='path to the file to interpret')
	argparser.add_argument('-v', '--verbose', action='store_true', help='show detailed debug messages')
	
	args = argparser.parse_args()
	
	VERBOSE = args.verbose

	context = {}
	context["variables"] = {}
	context["last named variable"] = None

	if args.filepath:
		# reading input file from argument
		with open(args.filepath) as f:
			processProgram(f.readline(), f, context)

	else:
		# fire up the rockstar shell
		rkshell.run_shell()
