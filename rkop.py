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
	'higher than' : 'GT',
	'greater than' : 'GT',
	'more than' : 'GT',
	'stronger than' : 'GT',
	'bigger than' : 'GT',

	'lower than' : 'LT',
	'less than' : 'LT',
	'weaker than' : 'LT',
	'smaller than' : 'LT',

	'as high as' : 'GE',
	'as big as' : 'GE',
	'as strong as' : 'GE',
	'as great as' : 'GE',
	'as beautiful as' : 'GE',

	'as low as' : 'LE',
	'as small as' : 'LE',
	'as weak as' : 'LE',
	'as bad as' : 'LE',
	'as little as' : 'LE',
	'as ugly as' : 'LE',

}

class TokenType:
	ARITHMETIC_OP = 'arithmetic operator'
	BOOLEAN_OP = 'comparator'
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