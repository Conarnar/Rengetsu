import discord
import rengetsu

def console(reng):
	guild = None
	channel = None

	while True:
		line = input()

		if line.strip().startswith('!'):
			args = line.split()
			if len(args) > 0:
				if args[0] == '!stop':
					break
				elif args[0] == '!status':
					if len(args) == 2:
						if args[1] in rengetsu.status_dict:
							reng.settings['status'] = args[1]
							reng.client.loop.create_task(reng.client.change_presence(status=rengetsu.status_dict[args[1]]))
							print(f'Status set to {args[1]}.')
							reng.save_settings()
							continue
					print('[Usage] !status (online|idle|dnd|invis)')
					continue
				elif args[0] == '!play':
					if len(args) == 1:
						reng.client.loop.create_task(reng.client.change_presence(activity=None))
						reng.settings['activity'] = ''
						print('Activity removed.')
						reng.save_settings()
						continue

					activity = line.split(maxsplit=1)[1]
					reng.settings['activity'] = activity
					reng.client.loop.create_task(reng.client.change_presence(activity=discord.Game(activity)))
					print(f'Activity set to {activity}.')
					reng.save_settings()
					continue
				elif args[0] == '!server':
					if len(args) == 1:
						print(', '.join(f'{guild.name} ({guild.id})' for guild in reng.client.guilds))
						continue
					elif len(args) == 2:
						try:
							guil = reng.client.get_guild(int(args[1]))
							if guil == None:
								print('No server with that id')
								continue
							guild = guil
							print(f'Joined {guild.name}')
							continue
						except ValueError:
							pass

					print('[Usage] !server [id]')
					continue
				elif args[0] == '!channel':
					if guild == None:
						print('Select a server first')
						continue

					if len(args) == 1:
						print(', '.join(f'#{channel.name} ({channel.id})' for channel in guild.channels if channel.type == discord.ChannelType.text))
						continue
					elif len(args) == 2:
						try:
							ch = guild.get_channel(int(args[1]))
							if ch == None or ch.type != discord.ChannelType.text:
								print('No text channel with that id')
								continue
							channel = ch
							reng.channel_id = channel.id
							print(f'Joined #{channel.name}')
							continue
						except ValueError:
							pass

					print('[Usage] !channel [id]')
					continue
				elif args[0] == '!members':
					if guild == None:
						print('Select a server first')
						continue

					print(', '.join(str(member) for member in guild.members))
					continue
				elif args[0] == '!back':
					if channel != None:
						print(f'Left channel {channel.name}')
						channel = None
						reng.channel_id = None
						continue

					if guild != None:
						print(f'Left server {guild.name}')
						guild = None
						continue

					print('You are not in any server')
					continue
			print('Unknown command')
		else:
			if channel == None:
				print('You are not in a channel')
				continue

			reng.client.loop.create_task(channel.send(f'**[Console]** {line}'))
	reng.client.loop.create_task(reng.client.close())