import commands
import random
import re

mr_re = re.compile(r'^(\d+)d(?:(\d+)|(\[.*\]))\s*(?:(\+|-)\s*(\d+))?\s*(.*)$')
drop_re = re.compile(r'^dl(\d*)(?:dh(\d*))?|dh(\d*)(?:dl(\d*))?$')
mod_re = re.compile(r'^(\+|-)\s*(\d+)$')

@commands.command(condition=lambda line : commands.first_arg_match(line, 'dice', 'd'))
async def command_dice(line, message, meta, reng):
	args = line.split()
	if len(args) == 2:
		try:
			i = int(args[1])

			if i > 0:
				return f'Rolled **{random.randint(1, i)}**.'
			else:
				return f'**[Error]** Arg 1 ({args[1]}) must be a positive integer.'
		except ValueError:
			return f'**[Error]** Arg 1 ({args[1]}) must be a positive integer.'
	elif len(args) == 3:
		try:
			i1 = int(args[1])
		except ValueError:
			return f'**[Error]** Arg 1 ({args[1]}) must be an integer.'
		try:
			i2 = int(args[2])
		except ValueError:
			return f'**[Error]** Arg 2 ({args[2]}) must be an integer.'
		return f'Rolled **{random.randint(min(i1, i2), max(i1, i2))}**.'
	return '**[Usage]** !dice <range> [range]'


@commands.command(condition=lambda line : commands.first_arg_match(line, 'multiroll', 'multi'))
async def command_multiroll(line, message, meta, reng):
	args = line.split()
	if len(args) == 3:
		try:
			i1 = int(args[1])

			if i1 <= 0 or i1 >= 500:
				return f'**[Error]** Arg 1 ({args[1]}) must be a positive integer less than 500.'
		except ValueError:
			return f'**[Error]** Arg 1 ({args[1]}) must be a positive integer less than 500.'
		
		try:
			i2 = int(args[2])

			if i2 <= 0:
				return f'**[Error]** Arg 2 ({args[2]}) must be a positive integer less than 500.'
		except ValueError:
			return f'**[Error]** Arg 2 ({args[2]}) must be a positive integer.'

		res = [random.randint(1, i2) for _ in range(i1)]
		return f"Rolled {', '.join(('**' + str(i) + '**') for i in res)} Total: **{sum(res)}**."
	elif len(args) == 4:
		try:
			i1 = int(args[1])

			if i1 <= 0 or i1 > 100:
				return f'**[Error]** Arg 1 ({args[1]}) must be a positive integer 100 or less.'
		except ValueError:
			return f'**[Error]** Arg 1 ({args[1]}) must be a positive integer 100 or less.'
		
		try:
			i2 = int(args[2])
		except ValueError:
			return f'**[Error]** Arg 2 ({args[2]}) must be an integer.'

		try:
			i3 = int(args[3])
		except ValueError:
			return f'**[Error]** Arg 3 ({args[3]}) must be an integer.'

		res = [random.randint(i2, i3) for _ in range(i1)]
		return f"Rolled {', '.join(('**' + str(i) + '**') for i in res)} Total: **{sum(res)}**."
	return '**[Usage]** !multiroll <amount> <range> [range]'

@commands.command(condition=lambda line : True)
async def command_xdy(line, message, meta, reng):
	match = mr_re.match(line)

	if match == None:
		raise commands.SkipCommand
	
	try:
		dice_count = int(match.group(1))

		if dice_count <= 0 or dice_count > 1000:
			return f'**[Error]** Dice count: {dice_count} must be a positive integer 1000 or less.'

		values = None

		if (match.group(2) == None):
			values = []
			weights = []
			val_len = 0

			roll = match.group(3)[1:-1]

			try:
				for lst in roll.split(','):
					comp = lst.split(':')

					if len(comp) == 1:
						val = int(comp[0])
						values.append(range(val, val + 1))
						weights.append(1)
						val_len += 1
					elif len(comp) == 2:
						i1 = int(comp[0])
						i2 = int(comp[1])
						rn = range(min(i1, i2), max(i1, i2) + 1)

						rn_len = rn.stop - rn.start
						values.append(rn)
						weights.append(rn_len)
						val_len += rn_len

				if len(values) == 0:
					return f'**[Error]** Invalid roll: d[{roll}].'
			except ValueError:
				return f'**[Error]** Invalid roll: d[{roll}].'
		else:
			roll = int(match.group(2))
			val_len = roll

			if roll <= 0:
				return f'**[Error]** Invalid roll: d{roll}.'

		mod = 0

		if match.group(4) and match.group(5):
			mod = int(match.group(4) + match.group(5))

		dl = 0
		dh = 0
		sort = False
		nosum = dice_count == 1 and mod == 0
		sumonly = False
		unique = False

		for option in match.group(6).split():
			drop_match = drop_re.match(option.lower())

			if drop_match != None:
				if drop_match.group(1) != None:
					dl = 1 if drop_match.group(1) == '' else int(drop_match.group(1))
					
					if drop_match.group(2) != None:
						dh = 1 if drop_match.group(2) == '' else int(drop_match.group(2))

				if drop_match.group(3) != None:
					dh = 1 if drop_match.group(3) == '' else int(drop_match.group(3))
					
					if drop_match.group(4) != None:
						dl = 1 if drop_match.group(4) == '' else int(drop_match.group(4))

				if dl + dh > dice_count:
					return '**[Error]** Cannot drop more dice than amount rolled.'
			elif option.lower() == 'sorted':
				sort = True
			elif option.lower() == 'nosum':
				if sumonly:
					return '**[Error]** Cannot use sumonly option with nosum option or when there is only one die.'

				nosum = True
			elif option.lower() == 'sumonly':
				if nosum:
					return '**[Error]** Cannot use sumonly option with nosum option or when there is only one die.'
				sumonly = True
			elif option.lower() == 'unique':
				unique = True

				if dice_count > val_len:
					return '**[Error]** Not enough possible values for unique option.'

				if val_len > 1000000000:
					return '**[Error]** Overflow: Cannot use more than 1000000000 die faces when using unique option.'
			else:
				return f'**[Error]** Unknown option: {option}.'


		if unique:
			if values == None:
				res = random.sample(range(1, roll + 1), dice_count)
			else:
				res = random.sample(sum((list(rn) for rn in values), []), dice_count)
		else:
			if values == None:
				res = [random.randint(1, roll) for _ in range(dice_count)]
			else:
				res = [random.randrange(rn.start, rn.stop) for rn in random.choices(values, weights, k=dice_count)]

		if sort:
			res.sort()

		dropped = set()
		if dl > 0:
			dropped.update(sorted(range(dice_count), key=lambda i: res[i])[:dl])
		if dh > 0:
			dropped.update(sorted(range(dice_count), key=lambda i: res[i], reverse=True)[:dh])

		if nosum:
			statement = f"Rolled {', '.join((('~~' if i in dropped else '**') + str(res[i]) + ('~~' if i in dropped else '**')) for i in range(dice_count))}."
		elif sumonly:
			statement = f"Total: **{sum(res[i] for i in range(dice_count) if i not in dropped) + mod}**."
		else:
			statement = f"Rolled {', '.join((('~~' if i in dropped else '**') + str(res[i]) + ('~~' if i in dropped else '**')) for i in range(dice_count))}"
			if mod != 0:
				statement += f', **(+{mod})**' if mod > 0 else f', **(-{-mod})**'
			statement += f" Total: **{sum(res[i] for i in range(dice_count) if i not in dropped) + mod}**."
		return statement
	except ValueError as e:
		raise commands.SkipCommand

@commands.command(condition=lambda line : commands.first_arg_match(line, 'percent', '%'))
async def command_percent(line, message, meta, reng):
	return f'Rolled **{random.randint(1, 100)}**.'