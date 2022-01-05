import commands
import asyncio
import discord
import emoji
import datetime
import time
import util

timer_dict = {}

def cancel(message):
	if message in timer_dict:
		timer_dict[message]['task'].cancel()
		del timer_dict[message]


@commands.menu(id_list=timer_dict)
async def menu_cancel(payload, reng):
	if payload.user_id != timer_dict[payload.message_id]['user_id']:
		return
	cancel(payload.message_id)

@commands.message_modify(id_list=timer_dict)
async def modify_cancel(message_id, reng):
	cancel(message_id)

async def timer(message_id, delay, reng):
	try:
		await asyncio.sleep(delay)
		del timer_dict[message_id]

		db = reng.db()
		cur = db.cursor()

		cur.execute('''
		SELECT t.channel_id, t.user_id, t.text, t.set_on
		FROM timer t
		WHERE t.message_id = ?
		''', (message_id,))

		row = cur.fetchone()
		
		if row != None:
			cur.execute('''
			DELETE FROM timer
			WHERE message_id = ?
			''', (message_id,))
			db.commit()

			channel_id, user_id, text, set_on = row
			embed = discord.Embed(title='Timer', description=text, timestamp=datetime.datetime.utcfromtimestamp(set_on))
			embed.set_footer(text='Set on:')
			await reng.client.http.send_message(channel_id, f'<@{user_id}>', embed=embed.to_dict())
	except asyncio.CancelledError:
		db = reng.db()
		cur = db.cursor()

		cur.execute('''
		SELECT t.channel_id, t.user_id
		FROM timer t
		WHERE t.message_id = ?
		''', (message_id,))

		row = cur.fetchone()
		
		if row != None:
			cur.execute('''
			DELETE FROM timer
			WHERE message_id = ?
			''', (message_id,))
			db.commit()
			
			channel_id, user_id = row
			await reng.client.http.send_message(channel_id, f'<@{user_id}> Your timer has been cancelled.')

@commands.command(condition=lambda line : commands.first_arg_match(line, 'timer'))
async def command_timer(line, message, meta, reng):
	if meta['len'] != 1:
		return '**[Error]** This command cannot be used with other commands in the same message.'
	
	args = line.split(maxsplit=2)

	if len(args) == 1:
		return '**[Usage]** !timer <time> [message]'
	delay = util.parse_time(args[1])
	if delay <= 0 or delay > 604800:
		return f'**[Error]** Arg 1 ({args[1]}) must represent time between 1 second and 1 week.'

	desc = args[2] if len(args) == 3 else 'Timer is done'
	now = time.time()

	db = reng.db()
	db.execute('''
	INSERT INTO timer(message_id, channel_id, user_id, text, set_on, end_on)
	VALUES (?, ?, ?, ?, ?, ?)
	''', (message.id, message.channel.id, message.author.id, desc, now, now + delay))
	db.commit()

	task = reng.client.loop.create_task(timer(message.id, delay, reng))
	timer_dict[message.id] = {'task': task, 'user_id': message.author.id}
	await message.add_reaction(emoji.X)
	return f'Timer has been set. Edit, delete, or {emoji.X} the original message to cancel.'

def on_load(reng):
	now = time.time()

	db = reng.db()
	cur = db.cursor()
	
	cur.execute('''
	DELETE FROM timer
	WHERE end_on < ?
	''', (now,))

	cur.execute('''
	SELECT t.channel_id, t.message_id, t.user_id, t.text, t.end_on, t.set_on
	FROM timer t
	''')

	db.commit()

	for channel_id, message_id, user_id, text, end_on, set_on in cur:
		task = reng.client.loop.create_task(timer(message_id, end_on - now, reng))
		timer_dict[message_id] = {'task': task, 'user_id': user_id}