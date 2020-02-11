import commands
import asyncio
import re
import discord
import emoji
import datetime
import time

time_regex = re.compile(r'(\d+)([dhms])')
time_to_seconds = {'d': 86400, 'h': 3600, 'm': 60, 's': 1}

timer_dict = {}

def cancel(message):
	if message in timer_dict:
		timer_dict[message][0].cancel()
		del timer_dict[message]


@commands.menu(id_list=timer_dict)
async def menu_cancel(payload, reng):
	if payload.user_id != timer_dict[payload.message_id][1]:
		return
	cancel(payload.message_id)

@commands.message_modify(id_list=timer_dict)
async def modify_cancel(message_id, reng):
	cancel(message_id)

def parse_time(string):
	try:
		return int(string)
	except ValueError:
		pass

	time = 0
	for match in time_regex.finditer(string.lower()):
		time += int(match.group(1)) * time_to_seconds[match.group(2)]
	return time

async def timer(channel_id, message_id, mention, desc, delay, set_on, reng):
	try:
		await asyncio.sleep(delay)
		embed = discord.Embed(title='Timer', description=desc, timestamp=datetime.datetime.utcfromtimestamp(set_on))
		embed.set_footer(text='Set on:')
		await reng.client.http.send_message(channel_id, mention, embed=embed.to_dict())
		del timer_dict[message_id]
	except asyncio.CancelledError:
		await reng.client.http.send_message(channel_id, f'{mention} Your timer has been cancelled')

@commands.command(condition=lambda line : commands.first_arg_match(line, 'timer'))
async def command_timer(line, message, meta, reng):
	args = line.split(maxsplit=2)

	if len(args) == 0:
		return '**[Usage]** !timer <time> [message]'
	delay = parse_time(args[1])
	if delay <= 0 or delay > 604800:
		return f'**[Argument Error]** Arg 1 ({args[1]}) must represent time between 1 second and 1 week'

	desc = args[2] if len(args) == 3 else 'Timer is done'
	now = time.time()
	task = reng.client.loop.create_task(timer(message.channel.id, message.id, message.author.mention, desc, delay, now, reng))
	timer_dict[message.id] = (task, message.author.id, message.channel.id, desc, now, now + delay)
	await message.add_reaction(emoji.X)
	return f'Timer has been set. Edit, delete, or {emoji.X} the original message to cancel.'

def on_load(reng):
	for timer_dat in reng.data.setdefault('timers', []):
		if timer_dat['end_on'] > time.time():
			task = reng.client.loop.create_task(timer(timer_dat['channel_id'], timer_dat['message_id'], f'<@{timer_dat["user_id"]}>', timer_dat['message'],
				timer_dat['end_on'] - time.time(), timer_dat['set_on'], reng))
			timer_dict[timer_dat['message_id']] = (task, timer_dat['user_id'], timer_dat['channel_id'], timer_dat['message'], timer_dat['set_on'], timer_dat['end_on'])

def on_save(reng):
	timers = []
	for key, value in timer_dict.items():
		timers.append({'message_id': key, 'user_id': value[1], 'channel_id': value[2], 'message': value[3], 'set_on': value[4], 'end_on': value[5]})
	reng.data['timers'] = timers