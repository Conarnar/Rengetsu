import discord
import logging
import os
import commands
import command_loader
import asyncio
import threading
import json
from datetime import datetime

class Rengetsu:
	def __init__(self, token):
		file = filename=datetime.now().strftime('reng_log/rengetsu_%Y_%m_%d_%H_%M_%S_%f.log')
		debug_file = 'reng_log/debug.log'
		os.makedirs(os.path.dirname(file), exist_ok=True)
		logging.basicConfig(level=logging.INFO, format='[%(asctime)s][%(levelname)s] %(name)s: %(message)s')
		logger = logging.getLogger('discord')
		handler = logging.FileHandler(file, encoding='utf-8', mode='w')
		handler.setFormatter(logging.Formatter('[%(asctime)s][%(levelname)s] %(name)s: %(message)s'))
		logger.addHandler(handler)

		self.token = token
		self.client = discord.Client()
		self.commands = []
		self.menus = []
		self.type_commands = []
		self.message_modifies = []
		self.logger = logger

		self.data_file = 'reng_dat/rengetsu.dat'
		self.data = {}

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

		self.save()
	
	async def saving(self):
		while True:
			await asyncio.sleep(3600)
			self.save()

	def save(self):
		command_loader.on_save(self)

		try:
			with open(self.data_file, 'w') as f:
				json.dump(self.data, f, indent=4)
			self.logger.info('Data successfully saved')
		except OSError as e:
			self.logger.error('Could not save data file:', e)


	def load_listeners(self):
		@self.client.event
		async def on_ready():
			self.logger.info(f'Logged on as {self.client.user}')

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
			if payload.member.bot:
				return

			for menu in self.menus:
				if payload.message_id in menu.menu_id_list:
					await self.client.http.remove_reaction(payload.channel_id, payload.message_id, payload.emoji, payload.user_id)
					await menu(payload, self)
					return

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
					await self.client.http.delete_message(message.channel.id, message.id, reason='Type command')
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