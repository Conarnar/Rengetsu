import discord
import logging
import os
import commands
import command_loader
import asyncio
import threading
import json
from datetime import datetime

status_dict = {'online': discord.Status.online, 'idle': discord.Status.idle, 'dnd': discord.Status.dnd, 'invis': discord.Status.invisible}

class Rengetsu:
	def __init__(self, settings):
		file = filename=datetime.now().strftime('reng_log/rengetsu_%Y_%m_%d_%H_%M_%S_%f.log')
		debug_file = 'reng_log/debug.log'
		os.makedirs(os.path.dirname(file), exist_ok=True)
		logging.basicConfig(level=logging.INFO, format='[%(asctime)s][%(levelname)s] %(name)s: %(message)s')
		logger = logging.getLogger('discord')
		handler = logging.FileHandler(file, encoding='utf-8', mode='w')
		handler.setFormatter(logging.Formatter('[%(asctime)s][%(levelname)s] %(name)s: %(message)s'))
		logger.addHandler(handler)
		logger = logging.getLogger('rengetsu')
		logger.addHandler(handler)

		self.token = settings['token']
		self.client = discord.Client(status=status_dict[settings.setdefault('status', 'online')], activity=discord.Game(settings.setdefault('activity', '')))
		self.commands = []
		self.menus = []
		self.type_commands = []
		self.message_modifies = []
		self.logger = logger

		self.data_file = 'reng_dat/rengetsu.dat'
		self.data = {}

		self.settings_file = 'reng_dat/settings.txt'
		self.settings = settings

		try:
			if (os.path.isfile(self.data_file)):
				with open(self.data_file) as f:
					self.data = json.load(f)
				logger.info('Data successfully loaded')
			else:
				logger.info('No data file found, using default')
		except (OSError, json.JSONDecodeError) as e:
			logger.error('Could not read data file:', e)
			logger.info('Resetting data to default')

	def run(self):
		command_loader.load_commands(self.commands)
		command_loader.load_menus(self.menus)
		command_loader.load_type_commands(self.type_commands)
		command_loader.load_message_modifies(self.message_modifies)
		self.load_listeners()

		loop = self.client.loop
		try:
			command_loader.on_load(self)
			loop.create_task(self.saving())
			loop.run_until_complete(self.client.start(self.token))
		except KeyboardInterrupt:
			loop.run_until_complete(self.client.logout())
		finally:
			loop.close()

		self.save_data()

	def console(self):
		while True:
			line = input()
			args = line.split()
			if len(args) > 0:
				if args[0] == 'stop':
					break
				elif args[0] == 'status':
					if len(args) == 2:
						if args[1] in status_dict:
							self.settings['status'] = args[1]
							self.client.loop.create_task(self.client.change_presence(status=status_dict[args[1]]))
							self.logger.info(f'Status set to {args[1]}.')
							self.save_settings()
							continue
					print('[Usage] status (online|idle|dnd|invis)')
					continue
				elif args[0] == 'play':
					if len(args) == 1:
						self.client.loop.create_task(self.client.change_presence(activity=None))
						self.settings['activity'] = ''
						self.logger.info('Activity removed.')
						self.save_settings()
						continue

					activity = line.split(maxsplit=1)[1]
					self.settings['activity'] = activity
					self.client.loop.create_task(self.client.change_presence(activity=discord.Game(activity)))
					self.logger.info(f'Activity set to {activity}.')
					self.save_settings()
					continue
			print('Unknown command')
		self.client.loop.create_task(self.client.logout())
	
	async def saving(self):
		await self.client.loop.run_in_executor(None, self.console);
		while True:
			await asyncio.sleep(3600)
			self.save_data()

	def save_data(self):
		command_loader.on_save(self)

		try:
			with open(self.data_file, 'w') as f:
				json.dump(self.data, f, indent=4)
			self.logger.info('Data successfully saved')
		except OSError as e:
			self.logger.error('Could not save data file:', e)

	def save_settings(self):
		try:
			with open(self.settings_file, 'w') as f:
				json.dump(self.settings, f, indent=4)
			self.logger.info('Settings successfully saved')
		except OSError as e:
			self.logger.error('Could not save settings file:', e)


	def load_listeners(self):
		@self.client.event
		async def on_ready():
			self.logger.info(f'Logged on as {self.client.user}')
			command_loader.on_login(self)

		async def on_message_modify(message_id):
			for message_modify in self.message_modifies:
				if message_id in message_modify.mm_id_list:
					await message_modify(message_id, self)
					return

		@self.client.event
		async def on_raw_bulk_message_delete(payload):
			for message in payload.message_ids:
				await on_message_modify(message)

		@self.client.event
		async def on_raw_message_delete(payload):
			await on_message_modify(payload.message_id)

		@self.client.event
		async def on_raw_message_edit(payload):
			await on_message_modify(payload.message_id)

		@self.client.event
		async def on_raw_reaction_add(payload):
			if payload.user_id == self.client.user.id:
				return

			for menu in self.menus:
				if payload.message_id in menu.menu_id_list:
					try:
						await self.client.http.remove_reaction(payload.channel_id, payload.message_id, payload.emoji, payload.user_id)
					except discord.errors.Forbidden:
						pass
					await menu(payload, self)
					return

		@self.client.event
		async def on_member_join(member):
			for k, v in self.data.setdefault('servers', {}).setdefault(str(member.guild.id), {}).setdefault('roles', {}).items():
				if v.setdefault('add_on_join', False):
					role = member.guild.get_role(int(k))
					if role != None:
						await member.add_roles(role, reason='Added on join')

		@self.client.event
		async def on_message(message):
			if message.author.bot:
				return

			if message.content == 'stop':
				await self.client.logout()
				return

			for type_command in self.type_commands:
				if (message.channel.id, message.author.id) in type_command.tc_id_list:
					await type_command(message, self)
					await self.client.http.delete_message(message.channel.id, message.id)
					return

			return_message = []

			cmds = [line.strip()[1:] for line in message.content.split('\n') if line.strip().startswith('!')]

			for line in cmds:
				for command in self.commands:
					if (command.condition(line)):
						try:
							ln = await command(line, message, {'len': len(cmds)}, self)
							if (ln != None):
								return_message.append(ln)
							break
						except commands.SkipCommand:
							pass

			send = None
			if (len(return_message) == 1):
				send = f'{message.author.mention} {return_message[0]}'
			elif (len(return_message) > 1):
				send = message.author.mention + '\n' + '\n'.join(return_message)
			if send != None:
				if len(send) > 2000:
					send = f'{message.author.mention} **[Message Error]** Message is too long to display (>2000 characters)'
				
				await message.channel.send(send)