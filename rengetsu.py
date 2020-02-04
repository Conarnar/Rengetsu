import discord
import logging
import os
from datetime import datetime

class Rengetsu:
	def __init__(self, token):
		if (not os.path.isdir('reng_log/')):
			os.mkdir('reng_log/')
		logging.basicConfig(level=logging.INFO, format='[%(asctime)s][%(levelname)s] %(name)s: %(message)s')
		logger = logging.getLogger('discord')
		handler = logging.FileHandler(filename=datetime.now().strftime('reng_log/rengetsu_%Y_%m_%d_%H_%M_%S_%f.log'), encoding='utf-8', mode='w')
		handler.setFormatter(logging.Formatter('[%(asctime)s][%(levelname)s] %(name)s: %(message)s'))
		logger.addHandler(handler)
		self._token = token
		self._client = discord.Client()

	def start(self):
		self.generate_listeners()
		self._client.run(self._token)

	def generate_listeners(self):
		@self._client.event
		async def on_ready():
			print('Logged on as', self._client.user)

		@self._client.event
		async def on_message(message):
			if message.content == 'stop':
				await self._client.logout()