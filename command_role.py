import commands
import emoji

main_menu_dict = {}
agreement_menu_dict = {}
add_remove_menu_dict = {}

agreement_editing_menu_dict = {}
add_remove_edit_dict = {}

@commands.menu(id_list=main_menu_dict)
async def menu_main(payload, reng):
	if payload.user_id != main_menu_dict[payload.message_id][0]:
		return

	role_dat = main_menu_dict[payload.message_id][1]
	extras = main_menu_dict[payload.message_id][2]
	edit = False

	if payload.emoji.name == emoji.BRIEFCASE:
		role_dat['add_on_join'] = not role_dat.setdefault('add_on_join', False)
		edit = True
	elif payload.emoji.name == emoji.GHOST:
		role_dat['add_on_inactive'] = not role_dat.setdefault('add_on_inactive', False)
		edit = True
	elif payload.emoji.name == emoji.ROBOT:
		role_dat['bot_permission'] = not role_dat.setdefault('bot_permission', False)
		edit = True
	elif payload.emoji.name == emoji.MEGAPHONE:
		role_dat['requestable'] = not role_dat.setdefault('requestable', False)
		role_dat['requestable_temp'] = False
		role_dat['requestable_agree'] = ''
		edit = True
	elif payload.emoji.name == emoji.CLOCK_2:
		if role_dat.setdefault('requestable', False):
			role_dat['requestable_temp'] = not role_dat.setdefault('requestable_temp', False)
			edit = True
	elif payload.emoji.name == emoji.PENCIL:
		if role_dat.setdefault('requestable', False):
			extras2 = {'agreement': role_dat.setdefault('requestable_agree', ''), 'editing': False}
			await reng.client.http.edit_message(payload.channel_id, payload.message_id, content=generate_message_agreement(role_dat, extras, reng, extras2))
			await reng.client.http.clear_reactions(payload.channel_id, payload.message_id)
			await reng.client.http.add_reaction(payload.channel_id, payload.message_id, emoji.PENCIL)
			await reng.client.http.add_reaction(payload.channel_id, payload.message_id, emoji.NO_ENTRY)
			await reng.client.http.add_reaction(payload.channel_id, payload.message_id, emoji.CHECKMARK)
			await reng.client.http.add_reaction(payload.channel_id, payload.message_id, emoji.CROSSMARK)
			agreement_menu_dict[payload.message_id] = main_menu_dict[payload.message_id] + (extras2,)
			del main_menu_dict[payload.message_id]
	elif payload.emoji.name == emoji.DOUBLE_ARROW_UP:
		extras2 = {'title': 'When this role is removed, these roles will be added:', 'editing': 0, 'list': list(role_dat.setdefault('add_when_this_role_remove', [])), 'type': False, 'guild': payload.guild_id}
		await reng.client.http.edit_message(payload.channel_id, payload.message_id, content=generate_message_add_remove(role_dat, extras, reng, extras2))
		await reng.client.http.clear_reactions(payload.channel_id, payload.message_id)
		await reng.client.http.add_reaction(payload.channel_id, payload.message_id, emoji.PLUS)
		await reng.client.http.add_reaction(payload.channel_id, payload.message_id, emoji.MINUS)
		await reng.client.http.add_reaction(payload.channel_id, payload.message_id, emoji.CHECKMARK)
		await reng.client.http.add_reaction(payload.channel_id, payload.message_id, emoji.CROSSMARK)
		add_remove_menu_dict[payload.message_id] = main_menu_dict[payload.message_id] + (extras2,)
		del main_menu_dict[payload.message_id]
	elif payload.emoji.name == emoji.DOUBLE_ARROW_DOWN:
		extras2 = {'title': 'When this role is added, these roles will be removed:', 'editing': 0, 'list': list(role_dat.setdefault('remove_when_this_role_add', [])), 'type': True, 'guild': payload.guild_id}
		await reng.client.http.edit_message(payload.channel_id, payload.message_id, content=generate_message_add_remove(role_dat, extras, reng, extras2))
		await reng.client.http.clear_reactions(payload.channel_id, payload.message_id)
		await reng.client.http.add_reaction(payload.channel_id, payload.message_id, emoji.PLUS)
		await reng.client.http.add_reaction(payload.channel_id, payload.message_id, emoji.MINUS)
		await reng.client.http.add_reaction(payload.channel_id, payload.message_id, emoji.CHECKMARK)
		await reng.client.http.add_reaction(payload.channel_id, payload.message_id, emoji.CROSSMARK)
		add_remove_menu_dict[payload.message_id] = main_menu_dict[payload.message_id] + (extras2,)
		del main_menu_dict[payload.message_id]
	elif payload.emoji.name == emoji.CHECKMARK:
		roles_dict = reng.data.setdefault('servers', {}).setdefault(str(payload.guild_id), {}).setdefault('roles', {})
		roles_dict[str(extras['id'])] = role_dat
		await reng.client.http.clear_reactions(payload.channel_id, payload.message_id)
		await reng.client.http.edit_message(payload.channel_id, payload.message_id, content=generate_message(role_dat, extras, reng, f'Saved {emoji.CHECKMARK}'))
		del main_menu_dict[payload.message_id]
	elif payload.emoji.name == emoji.CROSSMARK:
		await reng.client.http.clear_reactions(payload.channel_id, payload.message_id)
		await reng.client.http.edit_message(payload.channel_id, payload.message_id, content=generate_message(role_dat, extras, reng, f'Cancelled {emoji.CROSSMARK}'))
		del main_menu_dict[payload.message_id]
	elif payload.emoji.name == emoji.NO_ENTRY:
		roles_dict = reng.data.setdefault('servers', {}).setdefault(str(payload.guild_id), {}).setdefault('roles', {})
		if str(extras['id']) in roles_dict:
			del roles_dict[str(extras['id'])]
		await reng.client.http.clear_reactions(payload.channel_id, payload.message_id)
		await reng.client.http.edit_message(payload.channel_id, payload.message_id, content=generate_message(role_dat, extras, reng, f'Role data reset {emoji.NO_ENTRY}'))
		del main_menu_dict[payload.message_id]

	if edit:
		await reng.client.http.edit_message(payload.channel_id, payload.message_id, content=generate_message(role_dat, extras, reng))

@commands.type_command(id_list=add_remove_edit_dict)
async def type_command_add_remove(message, reng):
	message_id = add_remove_edit_dict[message.channel.id, message.author.id]
	
	role_dat = add_remove_menu_dict[message_id][1]
	extras = add_remove_menu_dict[message_id][2]
	extras2 = add_remove_menu_dict[message_id][3]

	guild = reng.client.get_guild(extras2['guild'])
	error = ''

	if extras2['editing'] == 1:
		new_roles = [role.id for role in guild.roles if role.name == message.content]
		if len(new_roles) == 0:
			error = '**[Error]** No role to add with that name, enter another role'
		else:
			del add_remove_edit_dict[message.channel.id, message.author.id]
			extras2['editing'] = 0
			extras2['list'].append(new_roles[0])
	else:
		new_list = [role for role in extras2['list'] if guild.get_role(role).name != message.content]
		if len(extras2['list']) == len(new_list):
			error = '**[Error]** No role to remove with that name, enter another role'
		else:
			del add_remove_edit_dict[message.channel.id, message.author.id]
			extras2['editing'] = 0
			extras2['list'] = new_list
	

	await reng.client.http.edit_message(message.channel.id, message_id, content=generate_message_add_remove(role_dat, extras, reng, extras2, error=error))

@commands.menu(id_list=add_remove_menu_dict)
async def menu_add_remove(payload, reng):
	if payload.user_id != add_remove_menu_dict[payload.message_id][0]:
		return
	
	role_dat = add_remove_menu_dict[payload.message_id][1]
	extras = add_remove_menu_dict[payload.message_id][2]
	extras2 = add_remove_menu_dict[payload.message_id][3]
	exit = False

	if payload.emoji.name == emoji.PLUS:
		if extras2['editing'] == 0:
			add_remove_edit_dict[(payload.channel_id, payload.user_id)] = payload.message_id
			extras2['editing'] = 1
			await reng.client.http.edit_message(payload.channel_id, payload.message_id, content=generate_message_add_remove(role_dat, extras, reng, extras2, error='Enter the role you want to add'))
	elif payload.emoji.name == emoji.MINUS:
		if extras2['editing'] == 0:
			add_remove_edit_dict[(payload.channel_id, payload.user_id)] = payload.message_id
			extras2['editing'] = 2
			await reng.client.http.edit_message(payload.channel_id, payload.message_id, content=generate_message_add_remove(role_dat, extras, reng, extras2, error='Enter the role you want to remove'))
	elif payload.emoji.name == emoji.CHECKMARK:
		if extras2['editing'] == 0:
			role_dat['remove_when_this_role_add' if extras2['type'] else 'add_when_this_role_remove'] = extras2['list']
			exit = True
	elif payload.emoji.name == emoji.CROSSMARK:
		if extras2['editing'] == 0:
			exit = True
		else:
			extras2['editing'] = 0
			await reng.client.http.edit_message(payload.channel_id, payload.message_id, content=generate_message_add_remove(role_dat, extras, reng, extras2))

	if exit:
		await reng.client.http.edit_message(payload.channel_id, payload.message_id, content=generate_message(role_dat, extras, reng))
		await reng.client.http.clear_reactions(payload.channel_id, payload.message_id)
		await reng.client.http.add_reaction(payload.channel_id, payload.message_id, emoji.BRIEFCASE)
		await reng.client.http.add_reaction(payload.channel_id, payload.message_id, emoji.GHOST)
		await reng.client.http.add_reaction(payload.channel_id, payload.message_id, emoji.ROBOT)
		await reng.client.http.add_reaction(payload.channel_id, payload.message_id, emoji.MEGAPHONE)
		await reng.client.http.add_reaction(payload.channel_id, payload.message_id, emoji.CLOCK_2)
		await reng.client.http.add_reaction(payload.channel_id, payload.message_id, emoji.PENCIL)
		await reng.client.http.add_reaction(payload.channel_id, payload.message_id, emoji.DOUBLE_ARROW_UP)
		await reng.client.http.add_reaction(payload.channel_id, payload.message_id, emoji.DOUBLE_ARROW_DOWN)
		await reng.client.http.add_reaction(payload.channel_id, payload.message_id, emoji.CHECKMARK)
		await reng.client.http.add_reaction(payload.channel_id, payload.message_id, emoji.CROSSMARK)
		await reng.client.http.add_reaction(payload.channel_id, payload.message_id, emoji.NO_ENTRY)
		main_menu_dict[payload.message_id] = add_remove_menu_dict[payload.message_id][:3]
		del add_remove_menu_dict[payload.message_id]

def generate_message_add_remove(role_dat, extras, reng, extras2, error=''):
	guild = reng.client.get_guild(extras2['guild'])
	extras2['list'] = [role for role in extras2['list'] if guild.get_role(role) != None]
	res = f'{extras["mention"]}\nRole: {extras["name"]} (id: {extras["id"]})\n'
	res += extras2['title'] + '\n' + ', '.join(guild.get_role(role).name for role in extras2['list'])
	if extras2['editing'] == 0:
		res += f'\n{error}\nAdd: {emoji.PLUS}          Remove: {emoji.MINUS}          Save: {emoji.CHECKMARK}          Cancel: {emoji.CROSSMARK}'
	else:
		res += f'\n{error}\nCancel: {emoji.CROSSMARK}'
	return res

@commands.type_command(id_list=agreement_editing_menu_dict)
async def type_command_agreement(message, reng):
	message_id = agreement_editing_menu_dict[message.channel.id, message.author.id]
	del agreement_editing_menu_dict[message.channel.id, message.author.id]
	
	role_dat = agreement_menu_dict[message_id][1]
	extras = agreement_menu_dict[message_id][2]
	extras2 = agreement_menu_dict[message_id][3]

	extras2['editing'] = False
	extras2['agreement'] = message.content

	await reng.client.http.edit_message(message.channel.id, message_id, content=generate_message_agreement(role_dat, extras, reng, extras2))

@commands.menu(id_list=agreement_menu_dict)
async def menu_agreement(payload, reng):
	if payload.user_id != agreement_menu_dict[payload.message_id][0]:
		return
	
	role_dat = agreement_menu_dict[payload.message_id][1]
	extras = agreement_menu_dict[payload.message_id][2]
	extras2 = agreement_menu_dict[payload.message_id][3]
	exit = False

	if payload.emoji.name == emoji.PENCIL:
		if not extras2['editing']:
			agreement_editing_menu_dict[(payload.channel_id, payload.user_id)] = payload.message_id
			extras2['editing'] = True
			await reng.client.http.edit_message(payload.channel_id, payload.message_id, content=generate_message_agreement(role_dat, extras, reng, extras2))
	elif payload.emoji.name == emoji.NO_ENTRY:
		if not extras2['editing']:
			extras2['agreement'] = ''
			await reng.client.http.edit_message(payload.channel_id, payload.message_id, content=generate_message_agreement(role_dat, extras, reng, extras2))
	elif payload.emoji.name == emoji.CHECKMARK:
		if not extras2['editing']:
			role_dat['requestable_agree'] = extras2['agreement']
			exit = True
	elif payload.emoji.name == emoji.CROSSMARK:
		if extras2['editing']:
			extras2['editing'] = False
			del agreement_editing_menu_dict[payload.channel_id, payload.user_id]
			await reng.client.http.edit_message(payload.channel_id, payload.message_id, content=generate_message_agreement(role_dat, extras, reng, extras2))
		else:
			exit = True

	if exit:
		await reng.client.http.edit_message(payload.channel_id, payload.message_id, content=generate_message(role_dat, extras, reng))
		await reng.client.http.clear_reactions(payload.channel_id, payload.message_id)
		await reng.client.http.add_reaction(payload.channel_id, payload.message_id, emoji.BRIEFCASE)
		await reng.client.http.add_reaction(payload.channel_id, payload.message_id, emoji.GHOST)
		await reng.client.http.add_reaction(payload.channel_id, payload.message_id, emoji.ROBOT)
		await reng.client.http.add_reaction(payload.channel_id, payload.message_id, emoji.MEGAPHONE)
		await reng.client.http.add_reaction(payload.channel_id, payload.message_id, emoji.CLOCK_2)
		await reng.client.http.add_reaction(payload.channel_id, payload.message_id, emoji.PENCIL)
		await reng.client.http.add_reaction(payload.channel_id, payload.message_id, emoji.DOUBLE_ARROW_UP)
		await reng.client.http.add_reaction(payload.channel_id, payload.message_id, emoji.DOUBLE_ARROW_DOWN)
		await reng.client.http.add_reaction(payload.channel_id, payload.message_id, emoji.CHECKMARK)
		await reng.client.http.add_reaction(payload.channel_id, payload.message_id, emoji.CROSSMARK)
		await reng.client.http.add_reaction(payload.channel_id, payload.message_id, emoji.NO_ENTRY)
		main_menu_dict[payload.message_id] = agreement_menu_dict[payload.message_id][:3]
		del agreement_menu_dict[payload.message_id]

def generate_message_agreement(role_dat, extras, reng, extras2):
	if extras2['editing']:
		return f'{extras["mention"]}\nRole: {extras["name"]} (id: {extras["id"]})\nEnter the new agreement\nCancel: {emoji.CROSSMARK}'

	res = f'{extras["mention"]}\nRole: {extras["name"]} (id: {extras["id"]})\n'

	agreement = extras2['agreement']

	if agreement == '':
		res += 'No agreement is required to request this role'
	else:
		res += f'Agreement:\n{agreement}'

	res += f'\nEdit: {emoji.PENCIL}          Delete: {emoji.NO_ENTRY}          Save: {emoji.CHECKMARK}          Cancel: {emoji.CROSSMARK}'
	return res

def generate_message(role_dat, extras, reng, ended=None):
	if ended != None:
		return f'{extras["mention"]}\nRole: {extras["name"]} (id: {extras["id"]})\n{ended}'

	res = f'{extras["mention"]}\nRole: {extras["name"]} (id: {extras["id"]})'

	if role_dat.setdefault('add_on_join', False):
		res += f'\nAdded to new members (Toggle: {emoji.BRIEFCASE})'
	else:
		res += f'\nNot added to new members (Toggle: {emoji.BRIEFCASE})'

	if role_dat.setdefault('add_on_inactive', False):
		res += f'\nAdded to inactive members (Toggle: {emoji.GHOST})'
	else:
		res += f'\nNot added to inactive members (Toggle: {emoji.GHOST})'

	if role_dat.setdefault('bot_permission', False):
		res += f'\nAllows usage of commands (Toggle: {emoji.ROBOT})'
	else:
		res += f'\nDoes not allow usage of commands (Toggle: {emoji.ROBOT})'

	if role_dat.setdefault('requestable', False):
		res += f'\nRequestable (Toggle: {emoji.MEGAPHONE})'

		if role_dat.setdefault('requestable_temp', False):
			res += f'\nTime argument required (Toggle: {emoji.CLOCK_2})'
		else:
			res += f'\nTime argument not required (Toggle: {emoji.CLOCK_2})'

		if role_dat.setdefault('requestable_agree', '') == '':
			res += f'\nNo agreement required (Manage: {emoji.PENCIL})'
		else:
			res += f'\nAgreement required (Manage: {emoji.PENCIL})'
	else:
		res += f'\nNot requestable (Toggle: {emoji.MEGAPHONE})'

	res += f'\n{len(role_dat.setdefault("add_when_this_role_remove", []))} roles will be added when this role is removed (Manage: {emoji.DOUBLE_ARROW_UP})'
	res += f'\n{len(role_dat.setdefault("remove_when_this_role_add", []))} roles will be removed when this role is added (Manage: {emoji.DOUBLE_ARROW_DOWN})'

	res += f'\nSave: {emoji.CHECKMARK}          Cancel: {emoji.CROSSMARK}          Reset: {emoji.NO_ENTRY}'
	return res

@commands.command(condition=lambda line : commands.first_arg_match(line, 'role'))
async def command_role(line, message, reng):
	if message.guild == None:
		return '**[Channel Error]** This command is only available in server channels'

	args = line.split()

	if len(args) != 2:
		return '**[Usage]** !roles <role name>'

	roles = [role for role in message.guild.roles if role.name == args[1]]

	if len(roles) == 0:
		return f'**[Argument Error]** No mentionable roles found with that name ({args[1]})'

	role_dat = reng.data.setdefault('servers', {}).setdefault(str(message.guild.id), {}).setdefault('roles', {}).setdefault(str(roles[0].id), {})
	extras = {'mention': message.author.mention, 'name': roles[0].name, 'id': roles[0].id}
	mes = await message.channel.send(generate_message(role_dat, extras, reng))
	main_menu_dict[mes.id] = (message.author.id, dict(role_dat), extras)
	await mes.add_reaction(emoji.BRIEFCASE)
	await mes.add_reaction(emoji.GHOST)
	await mes.add_reaction(emoji.ROBOT)
	await mes.add_reaction(emoji.MEGAPHONE)
	await mes.add_reaction(emoji.CLOCK_2)
	await mes.add_reaction(emoji.PENCIL)
	await mes.add_reaction(emoji.DOUBLE_ARROW_UP)
	await mes.add_reaction(emoji.DOUBLE_ARROW_DOWN)
	await mes.add_reaction(emoji.CHECKMARK)
	await mes.add_reaction(emoji.CROSSMARK)
	await mes.add_reaction(emoji.NO_ENTRY)
