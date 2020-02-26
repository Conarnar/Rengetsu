import commands
import util
import discord

@commands.command(condition=lambda line : commands.first_arg_match(line, 'settings'))
async def command_settings(line, message, meta, reng):
	if message.guild == None:
		return '**[Error]** This command is only available in server channels.'

	if not message.author.guild_permissions.administrator:
		return '**[Error]** You do not have permission to use this command.'

	args = line.split()

	settings = reng.data.setdefault('servers', {}).setdefault(str(message.guild.id), {}).setdefault('settings', {})

	if len(args) == 1:
		days = settings.setdefault('inactive', 0)
		log_channels = settings.setdefault('logging', [])
		log_channels = [channel_id for channel_id in log_channels if reng.client.get_channel(channel_id) != None]

		return '[Server settings]\n' + \
		('Inactive roles disabled.' if settings.setdefault('inactive', 0) == 0 else f'Inactivity period: {days} day{"s" if days > 1 else ""}.') + \
		'\n' + ('No logging channels.' if len(log_channels) == 0 else ('Logging channels: ' + ', '.join(f'<#{channel_id}>' for channel_id in log_channels) + '.'))

	if args[1] == 'inactive':
		if len(args) == 2:
			settings['inactive'] = 0
			return 'Inactive roles disabled'
		elif len(args) == 3:
			try:
				i = int(args[2])
				if i > 0:
					settings['inactive'] = i
					return f'Inactivity period set to {i} day{"s" if i > 1 else ""}.'
			except ValueError:
				pass

			return f'**[Error]** Arg 1 ({args[2]}) must be a positive integer.'
	elif args[1] == 'logging':
		if len(args) == 3 or len(args) == 4:
			if args[2] == 'add':
				if len(args) == 3:
					return '**[Usage]** !settings logging add <mention>'

				match = util.channel_mention_regex.fullmatch(args[3])

				if match == None:
					return f'**[Error]** Arg 3 ({args[3]}) must be a valid channel mention.'

				channel_id = int(match.group(1))

				channel = message.guild.get_channel(channel_id)

				if channel == None or channel.type != discord.ChannelType.text:
					return f'**[Error]** Arg 3 ({args[3]}) must be a valid channel mention.'

				log_channels = settings.setdefault('logging', [])

				if channel_id in log_channels:
					return f'**[Error]** That channel is already a logging channel.'

				log_channels.append(channel.id)

				return f'Added {channel.mention} as a logging channel.'
			elif args[2] == 'remove':
				if len(args) == 3:
					return '**[Usage]** !settings logging remove <mention>'

				match = util.channel_mention_regex.fullmatch(args[3])

				if match == None:
					return f'**[Error]** Arg 3 ({args[3]}) must be a valid channel mention.'

				channel_id = int(match.group(1))

				channel = message.guild.get_channel(channel_id)

				if channel == None or channel.type != discord.ChannelType.text:
					return f'**[Error]** Arg 3 ({args[3]}) must be a valid channel mention.'

				log_channels = settings.setdefault('logging', [])

				if channel_id not in log_channels:
					return f'**[Error]** That channel is not a logging channel.'

				log_channels.remove(channel.id)

				return f'Removed {channel.mention} as a logging channel.'

		return '**[Usage]** !settings logging <add|remove> <mention>'

	return f'**[Usage]** !settings [inactive|logging]'