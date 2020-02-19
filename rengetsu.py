import discord
import logging
import os
import commands
import command_loader
import asyncio
import threading
import json
import time
import console
from datetime import datetime

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

		self.channel_id = None

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
			loop.create_task(self.console_init())
			loop.create_task(self.saving())
			loop.create_task(self.inactivity())
			loop.run_until_complete(self.client.start(self.token))
		except KeyboardInterrupt:
			loop.run_until_complete(self.client.logout())
		finally:
			loop.close()

		self.save_data()

	async def console_init(self):
		await self.client.loop.run_in_executor(None, console.console, self)

	async def inactivity(self):
		while True:
			await asyncio.sleep(3600)
			now = time.time()

			for guild in self.client.guilds:
				guild_dat = self.data.setdefault('servers', {}).setdefault(str(guild.id), {})
				inactive_time = guild_dat.setdefault('settings', {}).setdefault('inactive', 0)
				if inactive_time == 0:
					continue

				members_dict = guild_dat.setdefault('members', {})
				roles_dict = guild_dat.setdefault('roles', {})

				to_add = {int(k) for k, v in roles_dict.items() if v.setdefault('add_on_inactive', False)}
				to_rem = set(sum([v.setdefault('remove_when_this_role_add', []) for k, v in roles_dict.items() if v.setdefault('add_on_inactive', False)], []))

				for member in guild.members:
					if now - members_dict.setdefault(str(member.id), {}).setdefault('last_msg', now) > inactive_time * 86400:
						for role_id in to_add:
							role = guild.get_role(role_id)
							if role != None and role not in member.roles:
								await member.add_roles(role, reason='Inactive')

						for role_id in to_rem:
							role = guild.get_role(role_id)
							if role != None and role in member.roles:
								await member.remove_roles(role, reason='Inactive')

	
	async def saving(self):
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
			if self.channel_id == message.channel.id:
				print(f'[{message.guild.name}#{message.channel.id}] {message.author}: {message.content}')

			if message.author.bot:
				return

			for type_command in self.type_commands:
				if (message.channel.id, message.author.id) in type_command.tc_id_list:
					await type_command(message, self)
					await self.client.http.delete_message(message.channel.id, message.id)
					return

			if message.guild != None:
				user_dat = self.data.setdefault('servers', {}).setdefault(str(message.guild.id), {}).setdefault('members', {}).setdefault(str(message.author.id), {})
				user_dat['last_msg'] = time.time()

				if not message.author.guild_permissions.administrator:
					roles = [int(k) for k, v in self.data['servers'][str(message.guild.id)].setdefault('roles', {}).items() if v.setdefault('bot_permission', False)]
					if len(roles) > 0:
						no_perms = True
						for role_id in roles:
							role = message.guild.get_role(role_id)
							if role in message.author.roles:
								no_perms = False
								break
						if no_perms:
							return

			return_message = []

			cmds = [line.strip()[1:] for line in message.content.split('\n') if line.strip().startswith('!')]

			for line in cmds:
				unknown = True
				for command in self.commands:
					if (command.condition(line)):
						try:
							ln = await command(line, message, {'len': len(cmds)}, self)
							if (ln != None):
								return_message.append(ln)
							unknown = False
							break
						except commands.SkipCommand:
							pass
				if unknown:
					return_message.append('**[Unknown Command]**')

			send = None
			if (len(return_message) == 1):
				send = f'{message.author.mention} {return_message[0]}'
			elif (len(return_message) > 1):
				send = message.author.mention + '\n' + '\n'.join(return_message)
			if send != None:
				if len(send) > 2000:
					send = f'{message.author.mention} **[Message Error]** Message is too long to display (>2000 characters)'
				
				await message.channel.send(send)