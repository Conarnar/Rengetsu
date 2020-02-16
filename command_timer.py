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

async def timer(channel_id, message_id, mention, desc, delay, set_on, reng):
	try:
		await asyncio.sleep(delay)
		del timer_dict[message_id]
		embed = discord.Embed(title='Timer', description=desc, timestamp=datetime.datetime.utcfromtimestamp(set_on))
		embed.set_footer(text='Set on:')
		await reng.client.http.send_message(channel_id, mention, embed=embed.to_dict())
	except asyncio.CancelledError:
		await reng.client.http.send_message(channel_id, f'{mention} Your timer has been cancelled')

@commands.command(condition=lambda line : commands.first_arg_match(line, 'timer'))
async def command_timer(line, message, meta, reng):
	if meta['len'] != 1:
		return '**[Message Error]** This command cannot be used with other commands in the same message'
	
	args = line.split(maxsplit=2)

	if len(args) == 0:
		return '**[Usage]** !timer <time> [message]'
	delay = util.parse_time(args[1])
	if delay <= 0 or delay > 604800:
		return f'**[Argument Error]** Arg 1 ({args[1]}) must represent time between 1 second and 1 week'

	desc = args[2] if len(args) == 3 else 'Timer is done'
	now = time.time()
	task = reng.client.loop.create_task(timer(message.channel.id, message.id, message.author.mention, desc, delay, now, reng))
	timer_dict[message.id] = {'task': task, 'user_id': message.author.id, 'message_id': message.id, 'channel_id': message.channel.id, 'message': desc,
		'set_on': now, 'end_on': now + delay}
	await message.add_reaction(emoji.X)
	return f'Timer has been set. Edit, delete, or {emoji.X} the original message to cancel.'

def on_load(reng):
	for timer_dat in reng.data.setdefault('timers', []):
		if timer_dat['end_on'] > time.time():
			task = reng.client.loop.create_task(timer(timer_dat['channel_id'], timer_dat['message_id'], f'<@{timer_dat["user_id"]}>', timer_dat['message'],
				timer_dat['end_on'] - time.time(), timer_dat['set_on'], reng))
			timer_dict[timer_dat['message_id']] = dict(timer_dat)
			timer_dict[timer_dat['message_id']].update({'task': task})
	
def on_save(reng):
	reng.data['timers'] = [{k: v for k, v in value.items() if k != 'task'} for value in timer_dict.values()]