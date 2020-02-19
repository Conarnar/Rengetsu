import commands

@commands.command(condition=lambda line : commands.first_arg_match(line, 'settings'))
async def command_settings(line, message, meta, reng):
	if message.guild == None:
		return '**[Channel Error]** This command is only available in server channels.'

	if not message.author.guild_permissions.administrator:
		return '**[Permission Error]** You do not have permission to use this command.'

	args = line.split()

	settings = reng.data.setdefault('servers', {}).setdefault(str(message.guild.id), {}).setdefault('settings', {})

	if len(args) == 1:
		return '[Sevrer settings]\n' + ('Inactive roles disabled.' if settings.setdefault('inactive', 0) == 0 else f'Inactivity period: {settings["inactive"]} day(s).')

	if args[1] == 'inactive':
		if len(args) == 2:
			settings['inactive'] = 0
			return 'Inactive roles disabled'
		elif len(args) == 3:
			try:
				i = int(args[2])
				if i > 0:
					settings['inactive'] = i
					return f'Inactivity period set to {i} day(s).'
			except ValueError:
				pass

			return f'**[Argument Error]** Arg 1 ({args[2]}) must be a positive integer.'

	return f'**[Usage]** !settings inactive <days>'