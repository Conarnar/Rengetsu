import commands
import discord

commands_list = {'dice': 'rolls dice', 'multiroll': 'rolls multiple dice', 'percent': 'generates a percentage',
'help': 'lists commands and usages', '>here': 'pings online users', 'math': 'perform calculations', '>role': 'manages roles',
'>request': 'requests a role', 'salt': 'currency commands', '>settings': 'manages server settings', 'timer': 'starts a timer'}

commands_usages = {
	'dice': {'!dice <max>': 'generates a number between 1 and <max>', '!dice <min> <max>': 'generates a number between <min> and <max>', 'Aliases': '!d'},
	'multiroll': {'!multiroll <amount> <max>': 'generates <amount> numbers between 1 and <max>',
		'!multiroll <amount> <min> <max>': 'generates <amount> numbers between <min> and <max>', 'Aliases': '!multi'},
	'percent': {'!percent': 'generates a number between 1 and 100', 'Aliases': '!%'},
	'help': {'!help': 'lists all commands', '!help <command>': 'explains the usage of <command>'},
	'here': {'!here <role>': 'pings everyone with <role> who is online', 'Aliases': '!ping'},
	'math': {'!math <expression>': 'calculates <expression>', 'Aliases': '!calc'},
	'role': {'!role <role>': 'opens a menu to manage <role>'},
	'request': {'!request <role>': 'requests to add or remove <role>', 'Aliases': '!requestrole'},
	'salt': {'!salt': 'tells you how much salt you have', '!salt claim': 'gives you more salt', '!salt gift <user> <amount>': 'gives <amount> salt to <user>'},
	'settings': {'!settings': 'lists the settings', '!settings inactive': 'disables setting users as inactive',
		'!settings inactive <time>': 'sets <time> days to set a user as inactive', '!settings usrlog add <channel>': 'adds <channel> as a user logging channel',
		'!settings usrlog remove <channel>': 'removes <channel> as a user logging channel', '!settings msglog add <channel>': 'adds <channel> as a message logging channel',
		'!settings msglog remove <channel>': 'removes <channel> as a message logging channel'},
	'timer': {'!timer <time>': 'sets a timer in <time>', '!timer <time> <message>': 'sets a timer in <time> that will tell you <message>'}
}

@commands.command(condition=lambda line : commands.first_arg_match(line, 'help'))
async def command_help(line, message, meta, reng):
	args = line.split(maxsplit=1)
	
	if meta['len'] != 1:
		return '**[Error]** This command cannot be used with other commands in the same message.'

	if len(args) == 1:
		inGuild = message.guild != None
		embed = discord.Embed(title='Commands List')
		for k, v in commands_list.items():
			if k[0] == '>':
				if inGuild:
					embed.add_field(name='!' + k[1:], value=v, inline=False)
			else:
				embed.add_field(name='!' + k, value=v, inline=False)
		await message.channel.send(f'{message.author.mention}', embed=embed)
		return


	if args[1] not in commands_usages:
		return '**[Usage]** !help [command]'

	embed = discord.Embed(title=f'Usage of !{args[1]}')
	for k, v in commands_usages[args[1]].items():
		embed.add_field(name=k, value=v, inline=False)
	await message.channel.send(f'{message.author.mention}', embed=embed)
	return