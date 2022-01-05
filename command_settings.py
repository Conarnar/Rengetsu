import commands
import util
import discord

@commands.command(condition=lambda line : commands.first_arg_match(line, 'settings'))
async def command_settings(line, message, meta, reng):
	if message.guild == None:
		return '**[Error]** This command is only available in server channels.'

	db = reng.db()
	cur = db.cursor()
	db.execute('''
	SELECT r.role_id
	FROM role r
	WHERE r.server_id = ? AND r.admin_permission = TRUE
	''', (message.guild.id,))
	roles = cur.fetchall()

	if not message.author.guild_permissions.administrator and not any((role.id,) in roles for role in message.author.roles):
		return '**[Error]** You do not have permission to use this command.'

	args = line.split()

	cur.execute('''
	INSERT OR IGNORE INTO server(server_id)
	VALUES (?)
	''', (message.guild.id,))
	db.commit()

	if len(args) == 1:
		cur.execute('''
		SELECT s.inactive_days
		FROM server s
		WHERE s.server_id = ?
		''', (message.guild.id,))

		inactive_days, = cur.fetchone()

		cur.execute('''
		SELECT c.channel_id
		FROM channel c
		WHERE c.server_id = ? AND c.user_log = TRUE
		''', (message.guild.id,))
		user_logs = cur.fetchall()

		cur.execute('''
		SELECT c.channel_id
		FROM channel c
		WHERE c.server_id = ? AND c.msg_log = TRUE
		''', (message.guild.id,))
		msg_logs = cur.fetchall()

		return '[Server settings]\n' + \
		('Inactive roles disabled.' if inactive_days == None else f'Inactivity period: {inactive_days} day{"s" if inactive_days > 1 else ""}.') + \
		'\n' + ('No user logging channels.' if len(user_logs) == 0 else ('User logging channels: ' + ', '.join(f'<#{channel_id}>' for channel_id, in user_logs) + '.')) + \
		'\n' + ('No message logging channels.' if len(msg_logs) == 0 else ('Message logging channels: ' + ', '.join(f'<#{channel_id}>' for channel_id, in msg_logs) + '.'))

	if args[1] == 'inactive':
		if len(args) == 2:
			cur.execute('''
			UPDATE server
			SET inactive_days = ?
			WHERE server_id = ?
			''', (None, message.guild.id))
			db.commit()

			return 'Inactive roles disabled'
		elif len(args) == 3:
			try:
				i = int(args[2])
				if i > 0:
					cur.execute('''
					UPDATE server
					SET inactive_days = ?
					WHERE server_id = ?
					''', (i, message.guild.id))
					db.commit()

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

				cur.execute('''
				SELECT c.user_log
				FROM channel c
				WHERE c.server_id = ? AND c.channel_id = ? 
				''', (message.guild.id, channel_id))
				is_log = cur.fetchall()

				if is_log and is_log[0][0]:
					return f'**[Error]** That channel is already a user logging channel.'

				if not is_log:
					cur.execute('''
					INSERT INTO channel(server_id, channel_id, user_log)
					VALUES (?, ?, TRUE)
					''', (message.guild.id, channel_id))
					db.commit()
				else:
					cur.execute('''
					UPDATE channel
					SET user_log = TRUE
					WHERE server_id = ? AND channel_id = ? 
					''', (message.guild.id, channel_id))
					db.commit()

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

				cur.execute('''
				SELECT c.user_log
				FROM channel c
				WHERE c.server_id = ? AND c.channel_id = ? 
				''', (message.guild.id, channel_id))
				is_log = cur.fetchall()

				cur.execute('''
				UPDATE channel
				SET user_log = FALSE
				WHERE server_id = ? AND channel_id = ? 
				''', (message.guild.id, channel_id))
				db.commit()

				if not is_log or not is_log[0][0]:
					return f'**[Error]** That channel is not a user logging channel.'

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

				cur.execute('''
				SELECT c.msg_log
				FROM channel c
				WHERE c.server_id = ? AND c.channel_id = ? 
				''', (message.guild.id, channel_id))
				is_log = cur.fetchall()

				if is_log and is_log[0][0]:
					return f'**[Error]** That channel is already a message logging channel.'

				if not is_log:
					cur.execute('''
					INSERT INTO channel(server_id, channel_id, msg_log)
					VALUES (?, ?, TRUE)
					''', (message.guild.id, channel_id))
					db.commit()
				else:
					cur.execute('''
					UPDATE channel
					SET msg_log = TRUE
					WHERE server_id = ? AND channel_id = ? 
					''', (message.guild.id, channel_id))
					db.commit()

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

				cur.execute('''
				SELECT c.msg_log
				FROM channel c
				WHERE c.server_id = ? AND c.channel_id = ? 
				''', (message.guild.id, channel_id))
				is_log = cur.fetchall()

				cur.execute('''
				UPDATE channel
				SET msg_log = FALSE
				WHERE server_id = ? AND channel_id = ? 
				''', (message.guild.id, channel_id))
				db.commit()

				if not is_log or not is_log[0][0]:
					return f'**[Error]** That channel is not a message logging channel.'

				return f'Removed {channel.mention} as a message logging channel.'

		return '**[Usage]** !settings msglog <add|remove> <mention>'

	return f'**[Usage]** !settings [inactive|usrlog|msglog]'