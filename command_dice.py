import commands
import random

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


@commands.command(condition=lambda line : commands.first_arg_match(line, 'multi'))
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
			i3 = int(args[2])
		except ValueError:
			return f'**[Error]** Arg 3 ({args[3]}) must be an integer.'

		res = [random.randint(i2, i3) for _ in range(i1)]
		return f"Rolled {', '.join(('**' + str(i) + '**') for i in res)} Total: **{sum(res)}**."
	return '**[Usage]** !multiroll <amount> <range> [range]'

@commands.command(condition=lambda line : len(line.split()) == 1)
async def command_multiroll_short(line, message, meta, reng):
	roll = line.split()[0].split('d')

	if len(roll) != 2:
		raise commands.SkipCommand
	
	try:
		i1 = int(roll[0])
		i2 = int(roll[1])

		if i1 <= 0 or i1 > 100:
			return f'**[Error]** Arg 1 ({i1}) must be a positive integer 100 or less.'

		res = [random.randint(1, i2) for _ in range(i1)]
		return f"Rolled {', '.join(('**' + str(i) + '**') for i in res)} Total: **{sum(res)}**."
	except ValueError:
		raise commands.SkipCommand

@commands.command(condition=lambda line : commands.first_arg_match(line, 'percent', '%'))
async def command_percent(line, message, meta, reng):
	return f'Rolled **{random.randint(1, 100)}**.'