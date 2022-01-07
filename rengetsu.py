import discord
import logging
import os
import database
import commands
import command_loader
import asyncio
import threading
import json
import time
import console
from datetime import datetime
import io

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
		self.client = discord.Client(status=status_dict[settings.setdefault('status', 'online')], activity=discord.Game(settings.setdefault('activity', '')), intents=discord.Intents.all())
		self.commands = []
		self.menus = []
		self.type_commands = []
		self.message_modifies = []
		self.logger = logger

		self.db_file = 'reng_dat/rengetsu.db'

		self.settings_file = 'reng_dat/settings.txt'
		self.settings = settings

		self.channel_id = None

		database.initialize_data(self.db_file, logger)

	def db(self):
		return database.create_connection(self.db_file)

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
			loop.create_task(self.salt_remind())
			loop.run_until_complete(self.client.start(self.token))
		except KeyboardInterrupt:
			loop.run_until_complete(self.client.logout())
		finally:
			loop.close()

	async def console_init(self):
		await self.client.loop.run_in_executor(None, console.console, self)

	async def inactivity(self):
		while True:
			await asyncio.sleep(3600)
			now = time.time()

			rows = sum(([(member.id, guild.id, now) for member in guild.members] for guild in self.client.guilds), [])
			db = self.db()
			cur = db.cursor()
			
			cur.executemany('''
			INSERT OR IGNORE INTO member(user_id, server_id, last_msg)
			VALUES (?, ?, ?)
			''', rows)
			db.commit()

			cur.execute('''
			SELECT s.server_id, s.inactive_days
			FROM server s
			WHERE s.inactive_days > 0
			''')

			for server_id, inactive_days in cur:
				guild = self.client.get_guild(server_id)
				if guild == None:
					continue

				cur2 = db.execute('''
				SELECT m.user_id
				FROM member m
				WHERE m.server_id = ? AND m.last_msg > ?
				''', (server_id, now - (inactive_days * 24 * 60 * 60)))

				cur3 = db.cursor() 

				to_add = cur3.execute('''
				SELECT r.role_id
				FROM role r
				WHERE r.server_id = ? AND r.add_on_inactive = TRUE
				''', (server_id,)).fetchall()
				to_remove = cur3.execute('''
				SELECT rm.to_remove_id
				FROM role r, role_remove_when_this_added rm
				WHERE r.server_id = ? AND r.add_on_inactive = TRUE AND r.role_id = rm.added_id
				''', (server_id,)).fetchall()

				for user_id, in cur2:
					member = guild.get_member(user_id)
					if member == None:
						continue
						
					for role_id, in to_add:
						role = guild.get_role(role_id)
						if role != None and role not in member.roles:
							await member.add_roles(role, reason='Inactive')

					for role_id, in to_rem:
						role = guild.get_role(role_id)
						if role != None and role in member.roles:
							await member.remove_roles(role, reason='Inactive')

	async def salt_remind(self):
		db = self.db()
		cur = db.cursor()

		while True:
			await asyncio.sleep(60)
			now = time.time()
			thresh = now - command_loader.command_salt.cooldown

			cur.execute('''
			SELECT u.user_id
			FROM user u
			WHERE u.salt_remind = TRUE AND u.salt_reminded = FALSE AND u.salt_last_claim < ?
			''', (thresh,))

			for user_id, in cur:
				try:
					user = self.client.get_user(user_id)
					if  user != None:
						await user.create_dm()
						await user.dm_channel.send(f'{user.mention} Your daily salt is ready to be claimed. Type `!salt claim` to do so.')
				except discord.errors.Forbidden:
					pass
			
			cur.execute('''
			UPDATE user
			SET salt_reminded = TRUE
			WHERE salt_remind = TRUE AND salt_reminded = FALSE AND salt_last_claim < ?
			''', (thresh,))

			db.commit()

	
	async def saving(self):
		while True:
			await asyncio.sleep(3600)

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

			if payload.guild_id == None:
				return
			
			db = self.db()
			msglog_channel_ids = db.execute('''
			SELECT c.channel_id
			FROM channel c
			WHERE c.server_id = ? AND c.msg_log = TRUE
			''', (payload.guild_id,)).fetchall()
			
			if (int(payload.channel_id),) in msglog_channel_ids:
				return

			msg = f"Message deleted from channel <#{payload.channel_id}>\n"

			cached = payload.cached_message

			if cached == None:
				msg += 'Message not found in cache'
			else:
				i = len(cached.attachments)
				msg += f'Author: {payload.cached_message.author.mention}\n'
				if i != 0:
					msg += f'Attachments: ' + ', '.join(attachment.filename for attachment in cached.attachments)
				msg += '\nMessage:'


			for channel_id, in msglog_channel_ids:
				channel = self.client.get_channel(channel_id)
				if channel != None:
					await channel.send(msg)
					if cached != None:
						files = []
						for attachment in cached.attachments:
							try:
								files.append(discord.File(io.BytesIO(await attachment.read(use_cached=True)), attachment.filename, spoiler=attachment.is_spoiler()))
							except:
								pass
						await channel.send(cached.content, files=files)

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
			db = self.db()
			cur = db.cursor()

			cur.execute('''
			INSERT OR IGNORE INTO user(user_id)
			VALUES (?)
			''', (member.id,))

			cur.execute('''
			INSERT OR IGNORE INTO member(user_id, server_id, last_msg)
			VALUES (?, ?, ?)
			''', (member.id, member.guild.id, time.time()))

			db.commit()

			cur.execute('''
			SELECT c.channel_id
			FROM channel c
			WHERE c.server_id = ? AND c.user_log = TRUE
			''', (member.guild.id,))

			for channel_id, in cur:
				channel = member.guild.get_channel(channel_id)
				if channel != None:
					await channel.send(f'{member.mention} (Username: {member}) has joined the server.')
			
			cur.execute('''
			SELECT r.role_id
			FROM role r
			WHERE r.server_id = ? AND r.add_on_join = TRUE
			''', (member.guild.id,))

			for role_id, in cur:
				role = member.guild.get_role(role_id)
				if role != None:
					await member.add_roles(role, reason='Added on join')

		@self.client.event
		async def on_member_remove(member):
			db = self.db()
			cur = db.cursor()

			cur.execute('''
			DELETE FROM member
			WHERE user_id = ? AND server_id = ?
			''', (member.id, member.guild.id))

			cur.execute('''
			SELECT c.channel_id
			FROM channel c
			WHERE c.server_id = ? AND c.user_log = TRUE
			''', (member.guild.id,))

			for channel_id, in cur:
				channel = member.guild.get_channel(channel_id)
				if channel != None:
					await channel.send(f'{member.mention} (Username: {member}) has left the server.')

		@self.client.event
		async def on_message(message):
			if self.channel_id == message.channel.id:
				print(f'[{message.guild.name}#{message.channel.id}] {message.author}: {message.content}')

			if message.author.bot:
				return

			for type_command in self.type_commands:
				if (message.channel.id, message.author.id) in type_command.tc_id_list:
					await type_command(message, self)
					try:
						await self.client.http.delete_message(message.channel.id, message.id)
					except discord.errors.Forbidden:
						pass
					return

			db = self.db()
			cur = db.cursor()

			cur.execute('''
			INSERT OR IGNORE INTO user(user_id)
			VALUES (?)
			''', (message.author.id,))

			if message.guild != None:
				cur.execute('''
				SELECT m.user_id
				FROM member m
				WHERE m.user_id = ? AND m.server_id = ?
				''', (message.author.id, message.guild.id))

				if cur.fetchall():
					cur.execute('''
					UPDATE member
					SET last_msg = ?
					WHERE user_id = ? AND server_id = ?
					''', (time.time(), message.author.id, message.guild.id))
				else:
					cur.execute('''
					INSERT INTO member(user_id, server_id, last_msg)
					VALUES (?, ?, ?)
					''', (message.author.id, message.guild.id, time.time()))
				db.commit()

				if message.guild != None and not message.author.guild_permissions.administrator:
					roles = cur.execute('''
					SELECT r.role_id
					FROM role r
					WHERE r.server_id = ? AND r.bot_permission = TRUE
					''', (message.guild.id,)).fetchall()
					if len(roles) > 0 and not any((role.id,) in roles for role in message.author.roles):
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

			send = '\n'.join(return_message)

			if len(send) > 0:
				if len(send) > 2000:
					send = f'{message.author.mention} **[Message Error]** Message is too long to display (>2000 characters)'
				
				await message.reply(send)