import math
import random
import commands

def iabs(i):
	return math.fabs(i) if type(i) == float else int(math.fabs(i))

functions = {'sqrt': math.sqrt, 'sin': math.sin, 'cos': math.cos, 'tan': math.tan, 'arcsin': math.asin, 'arccos': math.acos, 'arctan': math.atan,
'sinh': math.sinh, 'cosh': math.cosh, 'tanh': math.tanh, 'arcsinh': math.asinh, 'arccosh': math.acosh, 'arctanh': math.atanh,
'asin': math.asin, 'acos': math.acos, 'atan': math.atan, 'asinh': math.asinh, 'acosh': math.acosh, 'atanh': math.atanh,
'ceil': math.ceil, 'floor': math.floor, 'trunc': math.trunc,
'ln': math.log, 'abs': iabs}

class Calculator:
	def __init__(self, line):
		self._line = line.lower()
		self._dicerolls = []
		self._pos = -1
		self._char = '\0'
		self._value = self._parse()

	def value(self):
		return self._value

	def dicerolls(self):
		return self._dicerolls

	def _next_char(self):
		self._pos += 1
		self._char = self._line[self._pos] if self._pos < len(self._line) else '\0';

	def _eat(self, char_to_eat):
		while self._char.isspace():
			self._next_char()
		if self._char == char_to_eat:
			self._next_char()
			return True
		return False

	def _parse(self):
		self._next_char()
		x = self._parse_expression()
		if self._pos < len(self._line):
			raise ValueError(f'Unexpected: {self._char}')
		return x

	def _parse_expression(self):
		x = self._parse_term()
		while True:
			if self._eat('+'):
				x += self._parse_term()
			elif self._eat('-'):
				x -= self._parse_term()
			else:
				return x

	def _parse_term(self):
		x = self._parse_factor()
		while True:
			if self._eat('*'):
				x *= self._parse_factor()
			elif self._eat('/'):
				x /= self._parse_factor()
			elif self._eat('%'):
				x %= self._parse_factor()
			else:
				return x

	def _parse_factor(self):
		if self._eat('+'):
			return self._parse_factor()
		if self._eat('-'):
			return -self._parse_factor()

		startPos = self._pos

		if self._eat('('):
			x = self._parse_expression()
			self._eat(')')
		elif self._eat('|'):
			x = iabs(self._parse_expression())
			self._eat('|')
		elif ord('0') <= ord(self._char) <= ord('9') or ord(self._char) == ord('.'):
			while ord('0') <= ord(self._char) <= ord('9') or ord(self._char) == ord('.'):
				self._next_char()
			substr = self._line[startPos:self._pos]
			if '.' in substr:
				x = double(substr)
			else:
				x = int(substr)
		elif ord('a') <= ord(self._char) <= ord('z'):
			while ord('a') <= ord(self._char) <= ord('z'):
				self._next_char()
			substr = self._line[startPos:self._pos]
			x = self._parse_factor()
			if substr in functions:
				x = functions[substr](x)
			else:
				raise ValueError(f'Unknown function: {substr}')
		else:
			raise ValueError(f'Unexpected: {self._char}')

		if self._eat('^'):
			x = math.pow(x, self._parse_factor())
		elif self._eat('d'):
			z = math.floor(self._parse_factor())
			v = math.floor(x)
			res = [random.randint(1, z) for _ in range(v)]
			y = sum(res)
			self._dicerolls.append(f'{v}d{z}: ' + ', '.join(str(i) for i in res) + f' Total: {y}')
			x = y

		return x

@commands.command(condition=lambda line : commands.first_arg_match(line, 'calculate', 'math'))
async def command_calculate(line, message, meta, reng):
	try:
		calc = Calculator(line.strip()[5:])
		drs = calc.dicerolls()
		if len(drs) > 0:
			return f'Result: **{calc.value()}** [' + ' | '.join(drs) + ']'
		else:
			return f'Result: **{calc.value()}**'
	except ValueError as e:
		return f'**[Syntax Error]** {e}'
	except OverflowError as e:
		return f'**[Overflow Error]** {e}'