import math
import random
import commands
import re

functions = {'sqrt': math.sqrt, 'sin': math.sin, 'cos': math.cos, 'tan': math.tan, 'arcsin': math.asin, 'arccos': math.acos, 'arctan': math.atan,
'sinh': math.sinh, 'cosh': math.cosh, 'tanh': math.tanh, 'arcsinh': math.asinh, 'arccosh': math.acosh, 'arctanh': math.atanh,
'asin': math.asin, 'acos': math.acos, 'atan': math.atan, 'asinh': math.asinh, 'acosh': math.acosh, 'atanh': math.atanh,
'ceil': math.ceil, 'floor': math.floor, 'trunc': math.trunc,
'ln': math.log, 'abs': abs, 'rand': random.randrange, "fact": math.factorial}

mr_re = re.compile(r'(\d+)d(\d+)(?:d([lh])(\d*))?')
var_re = re.compile(r'^[_a-zA-Z][_\w]*')
sign_re = re.compile(r'([)\d\.])([-+])')
op_re = re.compile(r'[!=<>]=|[&|]{2}|[*\/^<>]')

class Calculator:
	def __init__(self, line, funcs={}, consts={}, args={}, yields=None, array=None):
		self._funcs = funcs
		self._consts = consts
		self._args = args
		self._yield = [] if yields == None else yields
		self._array = [0] * 100 if array == None else array
		self._ans = []
		self._exprs = [expr.strip() for expr in line.split(';')]
		self._value = None
		self._calculate()

	def _calculate(self):
		blocks = []
		line = 0
		loops = 0
		while line < len(self._exprs):
			if loops > 1000:
				raise OverflowError('Overflow Error: Max loops reached')
			loops += 1

			expr = self._exprs[line]

			match = var_re.match(expr)
			command = None if match == None else match.group()
			
			if command == 'end':
				if len(blocks) == 0:
					raise ValueError('Missing start of block')
				last = blocks.pop()
				if last[0] == 'end_on' or last[0] == 'skip_until':
					line += 1
					continue
				elif last[0] == 'loop':
					line = last[1]
					continue
			else:
				if len(blocks) > 0:
					if blocks[-1][0] == 'end_on':
						if command in blocks[-1][1]:
							blocks.pop()
							blocks.append(('skip_until', []))
					elif blocks[-1][0] == 'skip_until':
						if command in blocks[-1][1]:
							if command == 'else':
								blocks.pop()
								blocks.append(('end_on', []))
								line += 1
								continue
							elif command == 'elif':
								self._expr = expr[match.end():]
								if self._parse():
									blocks.pop()
									blocks.append(('end_on', ['else', 'elif']))
									line += 1
									continue
								else:
									line += 1
									continue
						else:
							line += 1
							continue

			if command == 'return':
				self._expr = expr[match.end():]
				if not self._expr.isspace() and self._expr != '':
					self._value = self._parse()

				break
			elif command == 'yield':
				print(expr)
				self._expr = expr[match.end():]
				value = self._parse()
				self._ans.append(value)
				self._yield.append(value)
				line += 1
				continue
			elif command == 'if':
				self._expr = expr[match.end():]
				if self._parse():
					blocks.append(('end_on', ['else', 'elif']))
					line += 1
					continue
				else:
					line += 1
					blocks.append(('skip_until', ['else', 'elif']))
					continue
			elif command == 'while':
				self._expr = expr[match.end():]
				if self._parse():
					blocks.append(('loop', line))
					line += 1
					continue
				else:
					line += 1
					blocks.append(('skip_until', []))
					continue
			else:
				self._expr = expr
				self._ans.append(self._parse())
				line += 1
				continue

	def value(self):
		return self._value

	def answers(self):
		return self._ans

	def yields(self):
		return self._yield

	def _next_char(self):
		self._pos += 1
		self._char = self._expr[self._pos] if self._pos < len(self._expr) else '\0';

	def _eat(self, char_to_eat):
		while self._char.isspace():
			self._next_char()
		if self._char == char_to_eat:
			self._next_char()
			return True
		return False

	def _parse(self):
		self._pos = -1
		self._next_char()
		x = self._parse_start()
		if self._pos < len(self._expr):
			raise ValueError(f'Syntax Error: Unexpected {self._char}')
		return x

	def _parse_start(self, short=False):
		return self._parse_or(short)

	def _parse_or(self, short=False):
		if short:
			self._parse_and(True)
			while True:
				if self._eat('|'):
					if self._char == '|':
						self._next_char()
						self._parse_and(True)
					else:
						raise ValueError(f'Syntax Error: Did you mean ||?')
				else:
					return

		x = self._parse_and()
		while True:
			if self._eat('|'):
				if self._char == '|':
					self._next_char()

					if x:
						x = 1
						self._parse_and(True)
					else:
						x = 1 if self._parse_and() else 0
				else:
					raise ValueError(f'Syntax Error: Did you mean ||?')
			else:
				return x

	def _parse_and(self, short=False):
		if short:
			self._parse_ineq(True)
			while True:
				if self._eat('&'):
					if self._char == '&':
						self._next_char()
						self._parse_ineq(True)
					else:
						raise ValueError(f'Syntax Error: Did you mean &&?')
				else:
					return

		x = self._parse_ineq()
		while True:
			if self._eat('&'):
				if self._char == '&':
					self._next_char()

					if not x:
						x = 0
						self._parse_ineq(True)
					else:
						x = 1 if self._parse_ineq() else 0
				else:
					raise ValueError(f'Syntax Error: Did you mean &&?')
			else:
				return x

	def _parse_ineq(self, short=False):
		if short:
			self._parse_expression(True)
			while True:
				if self._eat('<') or self._eat('>'):
					if self._char == '=':
						self._next_char()
					self._parse_expression(True)
				elif self._eat('='):
					if self._char == '=':
						self._next_char()
						self._parse_expression(True)
					else:
						raise ValueError(f'Syntax Error: Did you mean ==?')
				elif self._eat('!'):
					if self._char == '=':
						self._next_char()
						self._parse_expression(True)
					else:
						raise ValueError(f'Syntax Error: Did you mean !=?')
				else:
					return

		x = self._parse_expression()
		while True:
			if self._eat('<'):
				if self._char == '=':
					self._next_char()
					x = 1 if x <= self._parse_expression() else 0
				else:
					x = 1 if x < self._parse_expression() else 0
			elif self._eat('>'):
				if self._char == '=':
					self._next_char()
					x = 1 if x >= self._parse_expression() else 0
				else:
					x = 1 if x > self._parse_expression() else 0
			elif self._eat('='):
				if self._char == '=':
					self._next_char()
					x = 1 if x == self._parse_expression() else 0
				else:
					raise ValueError(f'Syntax Error: Did you mean ==?')
			elif self._eat('!'):
				if self._char == '=':
					self._next_char()
					x = 1 if x != self._parse_expression() else 0
				else:
					raise ValueError(f'Syntax Error: Did you mean !=?')
			else:
				return x

	def _parse_expression(self, short=False):
		if short:
			self._parse_term(True)
			while True:
				if self._eat('+') or self._eat('-'):
					self._parse_term(True)
				else:
					return

		x = self._parse_term()
		while True:
			if self._eat('+'):
				x += self._parse_term()
			elif self._eat('-'):
				x -= self._parse_term()
			else:
				return x

	def _parse_term(self, short=False):
		if short:
			self._parse_factor(True)
			while True:
				if self._eat('*') or self._eat('/') or self._eat('%'):
					self._parse_factor(True)
				else:
					return

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

	def _parse_factor(self, short=False):
		if short:
			self._parse_factor_short()
			return

		if self._eat('+'):
			return self._parse_factor()
		if self._eat('-'):
			return -self._parse_factor()
		if self._eat('!'):
			return 1 if not self._parse_factor() else 0

		startPos = self._pos

		if self._eat('('):
			x = self._parse_start()
			if not self._eat(')'):
				raise ValueError('Syntax Error: Missing )')
		elif ord('0') <= ord(self._char) <= ord('9') or ord(self._char) == ord('.'):
			while ord('0') <= ord(self._char) <= ord('9') or ord(self._char) == ord('.'):
				self._next_char()
			substr = self._expr[startPos:self._pos]
			if '.' in substr:
				x = float(substr)
			else:
				x = int(substr)
		elif ord('a') <= ord(self._char.lower()) <= ord('z') or self._char == '_':
			while ord('a') <= ord(self._char.lower()) <= ord('z') or ord('0') <= ord(self._char) <= ord('9') or self._char == '_':
				self._next_char()
			substr = self._expr[startPos:self._pos]
			
			if substr in self._args:
				x = self._args[substr]
			elif substr in self._consts:
				x = self._consts[substr]
			elif substr in self._funcs:
				args = self._parse_arguments()
				if args == None:
					raise ValueError('Syntax Error: Missing ( after function call')

				func = self._funcs[substr]
				params = func['args']

				if len(args) != len(params):
					raise ValueError(f'Syntax Error: Function {substr} takes {len(params)} argument{"" if len(params) == 1 else "s"} not {len(args)}')

				x = Calculator(func['expr'], funcs=self._funcs, consts=self._consts, args={params[i]: args[i] for i in range(len(params))}, yields=self._yield).value()
				if x == None:
					x = 0
			elif substr in functions:
				args = self._parse_arguments()

				if args == None:
					raise ValueError('Syntax Error: Missing ( after function call')
				if len(args) != 1:
					raise ValueError(f'Syntax Error: Function {substr} takes 1 argument not {len(args)}')

				x = functions[substr](args[0])
			elif substr == 'ans':
				args = self._parse_arguments()
				
				if args == None or len(args) == 0:
					x = self._ans[-1]
				else:
					if len(args) != 1:
						raise ValueError(f'Syntax Error: Function {substr} takes 1 argument not {len(args)}')
					x = self._ans[math.floor(args[0])]
			elif substr == 'sto':
				args = self._parse_arguments()

				if args == None:
					raise ValueError('Syntax Error: Missing ( after function call')
				if len(args) != 2:
					raise ValueError(f'Syntax Error: Function {substr} takes 2 arguments not {len(args)}')

				index = math.floor(args[0])

				if index < 0 or index >= 100:
					raise IndexError(f'Out of Bounds Error: Cannot store in index {index}')

				x = args[1]
				self._array[index] = x
			elif substr == 'rcl':
				args = self._parse_arguments()

				if args == None:
					raise ValueError('Syntax Error: Missing ( after function call')
				if len(args) != 1:
					raise ValueError(f'Syntax Error: Function {substr} takes 1 arguments not {len(args)}')

				index = math.floor(args[0])

				if index < 0 or index >= 100:
					raise IndexError(f'Out of Bounds Error: Cannot recall from index {index}')

				x = self._array[index]
			else:
				raise ValueError(f'Name Error: Unknown name {substr}')
		else:
			if self._char == '\0':
				raise ValueError('Syntax Error: Unexpected EOL')
			raise ValueError(f'Syntax Error: Unexpected {self._char}')

		if self._eat('^'):
			exp = self._parse_factor()
			if exp > 100:
				raise OverflowError(f'Overflow Error: Exponent ({exp}) greater than 100')
			x **= exp

		return x

	def _parse_factor_short(self):
		if self._eat('+') or self._eat('-') or self._eat('!'):
			self._parse_factor_short()
			return

		startPos = self._pos

		if self._eat('('):
			self._parse_start(True)
			if not self._eat(')'):
				raise ValueError('Syntax Error: Missing )')
		elif ord('0') <= ord(self._char) <= ord('9') or ord(self._char) == ord('.'):
			while ord('0') <= ord(self._char) <= ord('9') or ord(self._char) == ord('.'):
				self._next_char()
		elif ord('a') <= ord(self._char.lower()) <= ord('z') or self._char == '_':
			while ord('a') <= ord(self._char.lower()) <= ord('z') or ord('0') <= ord(self._char) <= ord('9') or self._char == '_':
				self._next_char()

			substr = self._expr[startPos:self._pos]
			
			if substr in self._args or substr in self._consts:
				pass
			elif substr in self._funcs:
				args = self._parse_arguments(True)
				if args == None:
					raise ValueError('Syntax Error: Missing ( after function call')

				func = self._funcs[substr]
				params = func['args']

				if len(args) != len(params):
					raise ValueError(f'Syntax Error: Function {substr} takes {len(params)} argument{"" if len(params) == 1 else "s"} not {len(args)}')
			elif substr in functions:
				args = self._parse_arguments(True)

				if args == None:
					raise ValueError('Syntax Error: Missing ( after function call')
				if len(args) != 1:
					raise ValueError(f'Syntax Error: Function {substr} takes 1 argument not {len(args)}')
			elif substr == 'ans':
				args = self._parse_arguments(True)
				
				if args != None and len(args) > 0:
					raise ValueError(f'Syntax Error: Function {substr} takes 1 argument not {len(args)}')
			else:
				raise ValueError(f'Name Error: Unknown name {substr}')
		else:
			if self._char == '\0':
				raise ValueError('Syntax Error: Unexpected EOL')
			raise ValueError(f'Syntax Error: Unexpected {self._char}')

		if self._eat('^'):
			self._parse_factor(True)

	def _parse_arguments(self, short=False):
		if not self._eat('('):
			return None

		if self._eat(')'):
			return []

		args = [self._parse_start(short)]

		while self._eat(','):
			args.append(self._parse_start(short))

		if not self._eat(')'):
			raise ValueError('Syntax Error: Missing )')

		return args

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

		func_dat = {}
		const_dat = {}

		calc = Calculator(expr, funcs=func_dat, consts=const_dat)
		results = calc.yields()
		if calc.value() != None:
			results.append(calc.value())
		if len(results) == 0:
			if len(calc.answers()) == 0:
				return '**[Error]** Nothing was calculated'
			else:
				results.append(calc.answers()[-1])

		res = ', '.join('**' + str(round(val, 10)) + '**' for val in results)

		expr = ''.join(expr.split())
		expr = op_re.sub(lambda match: f' {match.group(0)} ', expr)
		expr = sign_re.sub(lambda match: f'{match.group(1)} {match.group(2)} ', expr)

		if len(drs) > 0:
			return f'`{expr}` Result: {res} [' + ' | '.join(drs) + '].'
		else:
			return f'`{expr}` Result: {res}.'
	except Exception as e:
		return f'**[Error]** {e}.'