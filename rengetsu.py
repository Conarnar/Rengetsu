import discord
import logging
import os
import commands
import command_loader
import asyncio
import threading
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

		self._token = token
		self._client = discord.Client()
		self._commands = []
		self._logger = logger

	def start(self):
		command_loader.load_commands(self._commands)
		self.load_listeners()

		loop = self._client.loop
		try:
			loop.run_until_complete(self._client.start(self._token))
		except KeyboardInterrupt:
			loop.run_until_complete(self._client.logout())
		finally:
			loop.close()


	def load_listeners(self):
		@self._client.event
		async def on_ready():
			self._logger.info(f'Logged on as {self._client.user}')

		@self._client.event
		async def on_message(message):
			if message.author.bot:
				return

			if message.content == 'stop':
				await self._client.logout()
				return

			return_message = []
			for line in message.content.split('\n'):
				if line.startswith('!'):
					line = line[1:]
					for command in self._commands:
						if (command.condition(line)):
							try:
								ln = await command(line, message)
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
					await message.channel.send(f'{message.author.mention} **[Message Error]** Message is too long to display (>2000 characters)')
				else:
					await message.channel.send(send)