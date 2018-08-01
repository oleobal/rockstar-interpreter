import operator

FLOW_CONTROL_OPS = ("If", "While", "Until")

ARITHMETIC_OPS = {
	'times' : 	'MUL',
	'of' : 		'MUL',
	'plus' : 	'ADD',
	'with' : 	'ADD',
	'minus' : 	'SUB',
	'without' : 'SUB',
	'over' : 	'DIV'
}

CONDITIONAL_OPS = {
	'is higher than' : 'GT',
	'is greater than' : 'GT',
	'is more than' : 'GT',
	'is stronger than' : 'GT',
	'is bigger than' : 'GT',

	'is lower than' : 'LT',
	'is less than' : 'LT',
	'is weaker than' : 'LT',
	'is smaller than' : 'LT',

	'is as high as' : 'GE',
	'is as big as' : 'GE',
	'is as strong as' : 'GE',
	'is as great as' : 'GE',
	'is as beautiful as' : 'GE',

	'is as low as' : 'LE',
	'is as small as' : 'LE',
	'is as weak as' : 'LE',
	'is as bad as' : 'LE',
	'is as little as' : 'LE',
	'is as ugly as' : 'LE',

	'is as' : 'EQ',

	'is not as' : 'NE',
}

class TokenType:
	ARITHMETIC_OP = 'arithmetic operator'
	OP = 'operator'
	VAR = 'variable'
	LITERAL = 'literal'
	NUMBER = 'number'
	STRING = 'string'
	NONE = 'none'

arithmetic_operations = {
	'ADD' : 		operator.add,
	'MUL' : 		operator.mul,
	'SUB' : 		operator.sub,
	'DIV' : 		operator.truediv # or floordiv, like in C ?
}

conditional_operations = {
	'EQ' : operator.eq,
	'NE' : operator.ne,
	'LT' : operator.lt,
	'LE' : operator.le,
	'GT' : operator.gt,
	'GE' : operator.ge,
	'OR' : operator.or_,
	'AND': operator.and_,
	'TRUTH' : operator.truth,
	'NOT' : operator.__not__
}