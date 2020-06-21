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
		usrlogs = [channel_id for channel_id in log_channels if reng.client.get_channel(channel_id) != None]
		msglog_channels = settings.setdefault('msglog', [])
		msglogs = [channel_id for channel_id in msglog_channels if reng.client.get_channel(channel_id) != None]

		return '[Server settings]\n' + \
		('Inactive roles disabled.' if settings.setdefault('inactive', 0) == 0 else f'Inactivity period: {days} day{"s" if days > 1 else ""}.') + \
		'\n' + ('No user logging channels.' if len(usrlogs) == 0 else ('User logging channels: ' + ', '.join(f'<#{channel_id}>' for channel_id in usrlogs) + '.')) + \
		'\n' + ('No message logging channels.' if len(msglogs) == 0 else ('Message logging channels: ' + ', '.join(f'<#{channel_id}>' for channel_id in msglogs) + '.'))

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
	elif args[1] == 'usrlog':
		if len(args) == 3 or len(args) == 4:
			if args[2] == 'add':
				if len(args) == 3:
					return '**[Usage]** !settings usrlog add <mention>'

				match = util.channel_mention_regex.fullmatch(args[3])

				if match == None:
					return f'**[Error]** Arg 3 ({args[3]}) must be a valid channel mention.'

				channel_id = int(match.group(1))

				channel = message.guild.get_channel(channel_id)

				if channel == None or channel.type != discord.ChannelType.text:
					return f'**[Error]** Arg 3 ({args[3]}) must be a valid channel mention.'

				log_channels = settings.setdefault('logging', [])

				if channel_id in log_channels:
					return f'**[Error]** That channel is already a user logging channel.'

				log_channels.append(channel.id)

				return f'Added {channel.mention} as a user logging channel.'
			elif args[2] == 'remove':
				if len(args) == 3:
					return '**[Usage]** !settings usrlog remove <mention>'

				match = util.channel_mention_regex.fullmatch(args[3])

				if match == None:
					return f'**[Error]** Arg 3 ({args[3]}) must be a valid channel mention.'

				channel_id = int(match.group(1))

				channel = message.guild.get_channel(channel_id)

				if channel == None or channel.type != discord.ChannelType.text:
					return f'**[Error]** Arg 3 ({args[3]}) must be a valid channel mention.'

				log_channels = settings.setdefault('logging', [])

				if channel_id not in log_channels:
					return f'**[Error]** That channel is not a user logging channel.'

				log_channels.remove(channel.id)

				return f'Removed {channel.mention} as a user logging channel.'

		return '**[Usage]** !settings usrlog <add|remove> <mention>'
	elif args[1] == 'msglog':
		if len(args) == 3 or len(args) == 4:
			if args[2] == 'add':
				if len(args) == 3:
					return '**[Usage]** !settings msglog add <mention>'

				match = util.channel_mention_regex.fullmatch(args[3])

				if match == None:
					return f'**[Error]** Arg 3 ({args[3]}) must be a valid channel mention.'

				channel_id = int(match.group(1))

				channel = message.guild.get_channel(channel_id)

				if channel == None or channel.type != discord.ChannelType.text:
					return f'**[Error]** Arg 3 ({args[3]}) must be a valid channel mention.'

				msglog_channels = settings.setdefault('msglog', [])

				if channel_id in msglog_channels:
					return f'**[Error]** That channel is already a message logging channel.'

				msglog_channels.append(channel.id)

				return f'Added {channel.mention} as a message logging channel.'
			elif args[2] == 'remove':
				if len(args) == 3:
					return '**[Usage]** !settings msglog remove <mention>'

				match = util.channel_mention_regex.fullmatch(args[3])

				if match == None:
					return f'**[Error]** Arg 3 ({args[3]}) must be a valid channel mention.'

				channel_id = int(match.group(1))

				channel = message.guild.get_channel(channel_id)

				if channel == None or channel.type != discord.ChannelType.text:
					return f'**[Error]** Arg 3 ({args[3]}) must be a valid channel mention.'

				msglog_channels = settings.setdefault('msglog', [])

				if channel_id not in msglog_channels:
					return f'**[Error]** That channel is not a message logging channel.'

				msglog_channels.remove(channel.id)

				return f'Removed {channel.mention} as a message logging channel.'

		return '**[Usage]** !settings msglog <add|remove> <mention>'

	return f'**[Usage]** !settings [inactive|usrlog|msglog]'