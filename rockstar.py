import sys
import re

FLOW_CONTROL_OPS = ("If", "While", "Until")

class InputProgramError(Exception):
	pass

def raiseError(line, text):
	raise InputProgramError("Line : "+str(line)+"\nError : "+str(text))


def preProcessLine(line):
	"""
	Formatting to be done line per line, purely on text
	"""
	# removing comments
	line = re.sub(r"\(.*\)", "", line)
	# removing single quotes
	line = re.sub(r"'s\W+", " is ", line)
	line.replace("'", "")
	# removing whitespace
	line.strip()
	
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
			while line[i] != " ":
				newToken["value"]+=line[i]
				i+=1
			# this is actually not conform to the spec, which says all numbers should be DEC64
			# not like anyone will ever care enough
			try :
				newToken["value"] =  int(newToken["value"])
			except ValueError:
				pass
			try:
				newToken["value"] =  float(newToken["value"])
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
		
		
		# flow control
		
		global FLOW_CONTROL_OPS
		if nextWord in FLOW_CONTROL_OPS :
			tokenTree.append({"type":"flow control", "value":nextWord})
			i+=len(nextWord)
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
		
		# TODO poetic assignment
		
		# in this shitty language, is can either be initialisation or comparison
		# TODO comparison is
		if nextWord.lower() in ("is", "was", "were") :
			if tokenTree[-1]["type"] == "variable" :
				tokenTree.append({"type":"operator", "value":"poetic assignment"})
				
		
		# TODO treat all keywords before variables so the only thing left is variables
		
		# common variable
		
		if nextWord.lower() in ("a", "an", "the", "my", "your") :
			newToken["type"] = "variable"
			newToken["value"] = nextWord.lower()+" "
			i+=len(nextWord)+1
			nextWord = getNextWord(line,i)
			if nextWord.lower() != nextWord :
				raiseError(line, "Invalid common variable name")
			newToken["value"] += nextWord
			tokenTree.append(newToken)
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
	"""
	returns a tuple: 
	 (what an expression evaluates to, its type)
	types : "mysterious" (undefined), "null", "boolean", "number", "string", "object"
	
	:param expression: a tokenized tree (from tokenize())
	:param context:
	"""
	
	if type(expression) is list:
		resultingExpr = []
		for item in expression :
			resultingExpr.append(evaluate(item, context))
		# TODO compute expression here
		# for now just special case
		if len(resultingExpr) == 1:
			return resultingExpr[0]
	
	elif expression["type"] == "expression" :
		return evaluate(expression["value"], context)
	
	else:
		# Literals
		if expression["type"] in ("string", "number", "boolean")  :
			return (expression["value"], expression["type"])
		
		if expression["type"] == "variable" :
			return (context["variables"][expression["value"]]["value"], context["variables"][expression["value"]]["type"])
	
		# todo other types (boolean)
	
	
	# TODO poetic literals (in their own function ?)
	
	# TODO arithmetic, recursive expressions, etc
	
	
	
	return expression

def processInstruction(instruction, context):
	"""
	Execute instruction
	:param instruction: a tokenized tree
	"""

	
	# I/O
	
	if instruction[0]["value"] == "say" :
		print(str(evaluate(instruction[1:], context)[0]))
	
	# Variable assignment
	
	if instruction[0]["value"] == "assignment put" :
		# it should go instruction : (0) put (1) expression (2) into (3) variable
		v, t = evaluate(instruction[1], context)
		context["variables"][instruction[3]["value"]] = {}
		context["variables"][instruction[3]["value"]]["value"] = v
		context["variables"][instruction[3]["value"]]["type"] = t
	

	# TODO
	



def processTextBlock(line, fileobject, context, isTopLevelBlock=False):
	"""
	An instruction is typically a single line, but multiline instruction (whiles..) exist and in this case we wait for the end of the block to execute it in its entirety. The obvious exception is the top level block
	
	:param line: first line of the block
	:param fileobject: current TextIOWrapper
	:param context: the program context
	:param isTopLevelBlock: call with True, False is for recursion
	"""
	
	
	while line != "" :
	
		# end of block
		if line.strip() == "":
			if isTopLevelBlock:
				line = f.readline()
				continue
			else:
				break
		
		instruction = preProcessLine(line)
		instruction = tokenize(instruction)
		
		
		
		# sub block
		global FLOW_CONTROL_OPS
		if instruction[0]["value"] in FLOW_CONTROL_OPS:
			line = f.readline()
			instruction += processTextBlock(line, f, context)
		
		
		
		# instruction
		processInstruction(instruction, context)
			
			
		line = f.readline()
	
	return instruction

if __name__ == '__main__':
	context = {}
	context["variables"] = {}

	# reading input file from argument
	with open(sys.argv[1]) as f:
		l = f.readline()
		processTextBlock(l, f, context, isTopLevelBlock=True)





class Variable :
	def __init__(self, name, type='mysterious'):
		self.name = name
		self.setType(type)
	