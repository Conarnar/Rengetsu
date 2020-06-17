import math
import random
import commands
import re

functions = {'sqrt': math.sqrt, 'sin': math.sin, 'cos': math.cos, 'tan': math.tan, 'arcsin': math.asin, 'arccos': math.acos, 'arctan': math.atan,
'sinh': math.sinh, 'cosh': math.cosh, 'tanh': math.tanh, 'arcsinh': math.asinh, 'arccosh': math.acosh, 'arctanh': math.atanh,
'asin': math.asin, 'acos': math.acos, 'atan': math.atan, 'asinh': math.asinh, 'acosh': math.acosh, 'atanh': math.atanh,
'ceil': math.ceil, 'floor': math.floor, 'trunc': math.trunc,
'ln': math.log, 'abs': abs}

mr_re = re.compile(r'(\d+)d(\d+)(?:d([lh])(\d*))?')

class Calculator:
	def __init__(self, line):
		self._line = line.lower()
		self._pos = -1
		self._char = '\0'
		self._value = self._parse()

	def value(self):
		return self._value

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
				y = self._parse_factor()

				if type(x) == int and type(y) == int and x % y == 0:
					x //= y
				else:
					x /= y
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
			x = abs(self._parse_expression())
			self._eat('|')
		elif ord('0') <= ord(self._char) <= ord('9') or ord(self._char) == ord('.'):
			while ord('0') <= ord(self._char) <= ord('9') or ord(self._char) == ord('.'):
				self._next_char()
			substr = self._line[startPos:self._pos]
			if '.' in substr:
				x = float(substr)
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
			x **= self._parse_factor()

		return x

@commands.command(condition=lambda line : commands.first_arg_match(line, 'math', 'calc'))
async def command_math(line, message, meta, reng):
	try:
		drs = []
		expr = line.strip()[5:]
		match = mr_re.search(expr)
		while match != None:
			i1 = int(match.group(1))
			i2 = int(match.group(2))

			if i1 > 100:
				return f'**[Error]** Diceroll Error [{match.group()}], Arg 1 ({i1}) cannot be greater than 100.'

			if i2 <= 0:
				return f'**[Error]** Diceroll Error [{match.group()}], Arg 2 ({i2}) must be greater than 0.'

			if match.group(4) != None:
				if match.group(4) == '':
					i3 = 1
				else:
					i3 = min(int(match.group(4)), i1)

			res = [random.randint(1, i2) for _ in range(i1)]

			dropped = set()
			if match.group(3) != None:
				dropped = set(sorted(range(i1), key=lambda i: res[i], reverse=match.group(3) != 'l')[:i3])

			total = sum(res[i] for i in range(i1) if i not in dropped)
			drs.append(f"{i1}d{i2}{'' if match.group(3) == None else 'd' + match.group(3) + str(i3)}: {', '.join((('~~' if i in dropped else '') + str(res[i]) + ('~~' if i in dropped else '')) for i in range(i1))} Total: {total}")
			expr = expr[:match.start()] + f' {total} ' + expr[match.end():]
			match = mr_re.search(expr)


		calc = Calculator(expr)

		if len(drs) > 0:
			return f'Result: **{round(calc.value(), 10)}** [' + ' | '.join(drs) + '].'
		else:
			return f'Result: **{round(calc.value(), 10)}**.'
	except ValueError as e:
		return f'**[Error]** SyntaxError: {e}.'
	except OverflowError as e:
		return f'**[Error]** OverflowError: {e}.'