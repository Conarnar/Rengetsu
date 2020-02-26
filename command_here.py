import commands
import discord

@commands.command(condition=lambda line: commands.first_arg_match(line, 'here', 'ping'))
async def command_here(line, message, meta, reng):
	if message.guild == None:
		return '**[Error]** This command is only available in server channels.'

	args = line.split()

	if (len(args) != 2):
		return '**[Usage]** !here <role name>'

	roles = [role for role in message.guild.roles if role.name == args[1] and role.mentionable]

	if (len(roles) == 0):
		return f'**[Error]** No mentionable roles found with that name ({args[1]}).'

	return 'Pinging ' + ' '.join(member.mention for member in message.guild.members if member.status != discord.Status.offline and any(role in member.roles for role in roles)) + '.'