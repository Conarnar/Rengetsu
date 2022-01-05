import commands
import emoji
import util
import discord
import time
import asyncio

main_menu_dict = {}
agreement_menu_dict = {}
add_remove_menu_dict = {}

agreement_editing_menu_dict = {}
add_remove_edit_dict = {}

agreement_pending_dict = {}

timer_dict = {}


@commands.menu(id_list=agreement_pending_dict)
async def menu_agreement_pending(payload, reng):
	pend_dict = agreement_pending_dict[payload.message_id]
	if payload.user_id != pend_dict['user_id']:
		return

	del agreement_pending_dict[payload.message_id]

	if payload.emoji.name == emoji.CHECKMARK:
		try:
			await reng.client.http.add_role(pend_dict['guild_id'], pend_dict['user_id'], pend_dict['role_id'], reason='Requested')
			await reng.client.http.edit_message(payload.channel_id, payload.message_id, content=pend_dict['agreement'] + '\n**[Accepted]**')

			db = reng.db()
			cur = db.cursor()
			cur.execute('''
			SELECT r.to_remove_id
			FROM role_remove_when_this_added r
			WHERE r.added_id = ?
			''', (pend_dict['role_id'],))
			remove_when_this_role_add = [to_remove_id for to_remove_id, in cur]

			for remove_id in remove_when_this_role_add:
				try:
					await reng.client.http.remove_role(pend_dict['guild_id'], pend_dict['user_id'], remove_id, reason=f'Removed upon adding id({pend_dict["role_id"]})')
				except discord.errors.NotFound:
					pass

		except discord.errors.NotFound:
			await reng.client.http.edit_message(payload.channel_id, payload.message_id, content=pend_dict['agreement'] + '\n**[Error]** Role deleted')

		await reng.client.http.remove_reaction(payload.channel_id, payload.message_id, emoji.CHECKMARK, reng.client.user.id)
		await reng.client.http.remove_reaction(payload.channel_id, payload.message_id, emoji.CROSSMARK, reng.client.user.id)
	elif payload.emoji.name == emoji.CROSSMARK:
		await reng.client.http.edit_message(payload.channel_id, payload.message_id, content=pend_dict['agreement'] + '\n**[Declined]**')
		await reng.client.http.remove_reaction(payload.channel_id, payload.message_id, emoji.CHECKMARK, reng.client.user.id)
		await reng.client.http.remove_reaction(payload.channel_id, payload.message_id, emoji.CROSSMARK, reng.client.user.id)

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
	elif payload.emoji.name == emoji.CROWN:
		role_dat['admin_permission'] = not role_dat.setdefault('admin_permission', False)
		edit = True
	elif payload.emoji.name == emoji.MEGAPHONE:
		role_dat['requestable'] = not role_dat.setdefault('requestable', False)
		role_dat['requestable_temp'] = False
		role_dat['requestable_agree'] = ''
		edit = True
	elif payload.emoji.name == emoji.CLOCK_2:
		if role_dat.setdefault('requestable', False):
			if role_dat.setdefault('requestable_temp', False):
				role_dat['requestable_temp'] = False
			else:
				role_dat['requestable_temp'] = True
				role_dat['requestable_agree'] = ''
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
		db = reng.db()
		cur = db.cursor()
		cur.execute('''
		DELETE FROM role
		WHERE role_id = ?
		''', (extras['id'],))

		cur.execute('''
		DELETE FROM role_requestable
		WHERE role_id = ?
		''', (extras['id'],))

		cur.execute('''
		DELETE FROM role_add_when_this_removed
		WHERE removed_id = ?
		''', (extras['id'],))

		cur.execute('''
		DELETE FROM role_remove_when_this_added
		WHERE added_id = ?
		''', (extras['id'],))

		cur.execute('''
		INSERT INTO role(role_id, server_id, add_on_join, add_on_inactive, bot_permission, admin_permission)
		VALUES (?, ?, ?, ?, ?, ?)
		''', (extras['id'], payload.guild_id, role_dat['add_on_join'], role_dat['add_on_inactive'], role_dat['bot_permission'], role_dat['admin_permission']))

		if role_dat['requestable']:
			cur.execute('''
			INSERT INTO role_requestable(role_id, temp, agreement)
			VALUES (?, ?, ?)
			''', (extras['id'], role_dat['requestable_temp'], role_dat['requestable_agree']))
		
		cur.executemany('''
		INSERT INTO role_add_when_this_removed(removed_id, to_add_id)
		VALUES (?, ?)
		''', [(extras['id'], add_id) for add_id in role_dat['add_when_this_role_remove']])
		
		cur.executemany('''
		INSERT INTO role_remove_when_this_added(added_id, to_remove_id)
		VALUES (?, ?)
		''', [(extras['id'], remove_id) for remove_id in role_dat['remove_when_this_role_add']])

		db.commit()
		await reng.client.http.clear_reactions(payload.channel_id, payload.message_id)
		await reng.client.http.edit_message(payload.channel_id, payload.message_id, content=generate_message(role_dat, extras, reng, f'Saved {emoji.CHECKMARK}'))
		del main_menu_dict[payload.message_id]
	elif payload.emoji.name == emoji.CROSSMARK:
		await reng.client.http.clear_reactions(payload.channel_id, payload.message_id)
		await reng.client.http.edit_message(payload.channel_id, payload.message_id, content=generate_message(role_dat, extras, reng, f'Cancelled {emoji.CROSSMARK}'))
		del main_menu_dict[payload.message_id]
	elif payload.emoji.name == emoji.NO_ENTRY:
		db = reng.db()
		cur = db.cursor()
		cur.execute('''
		DELETE FROM role
		WHERE role_id = ?
		''', (extras['id'],))
		db.commit()
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
			error = '**[Error]** No role to add with that name, enter another role.'
		else:
			del add_remove_edit_dict[message.channel.id, message.author.id]
			extras2['editing'] = 0
			extras2['list'].append(new_roles[0])
	else:
		new_list = [role for role in extras2['list'] if guild.get_role(role).name != message.content]
		if len(extras2['list']) == len(new_list):
			error = '**[Error]** No role to remove with that name, enter another role.'
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
		await reng.client.http.add_reaction(payload.channel_id, payload.message_id, emoji.CROWN)
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
			if role_dat['requestable_agree'] != '':
				role_dat['requestable_temp'] = False
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
		await reng.client.http.add_reaction(payload.channel_id, payload.message_id, emoji.CROWN)
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

	if role_dat.setdefault('admin_permission', False):
		res += f'\nAllows usage of admin commands (Toggle: {emoji.CROWN})'
	else:
		res += f'\nDoes not allow usage of admin commands (Toggle: {emoji.CROWN})'

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

	guild = reng.client.get_guild(extras['guild_id'])
	awr = [role_id for role_id in role_dat.setdefault('add_when_this_role_remove', []) if guild.get_role(role_id) != None]
	rwa = [role_id for role_id in role_dat.setdefault('remove_when_this_role_add', []) if guild.get_role(role_id) != None]
	role_dat['add_when_this_role_remove'] = awr
	role_dat['remove_when_this_role_add'] = rwa
	res += f'\n{len(awr)} roles will be added when this role is removed (Manage: {emoji.DOUBLE_ARROW_UP})'
	res += f'\n{len(rwa)} roles will be removed when this role is added (Manage: {emoji.DOUBLE_ARROW_DOWN})'

	res += f'\nSave: {emoji.CHECKMARK}          Cancel: {emoji.CROSSMARK}          Reset: {emoji.NO_ENTRY}'
	return res

@commands.command(condition=lambda line : commands.first_arg_match(line, 'role'))
async def command_role(line, message, meta, reng):
	if message.guild == None:
		return '**[Error]** This command is only available in server channels.'

	db = reng.db()
	cur = db.cursor()
	cur.execute('''
	SELECT r.role_id
	FROM role r
	WHERE r.server_id = ? AND r.admin_permission = TRUE
	''', (message.guild.id,))
	roles = cur.fetchall()

	if not message.author.guild_permissions.administrator and not any((role.id,) in roles for role in message.author.roles):
		return '**[Error]** You do not have permission to use this command.'

	if meta['len'] != 1:
		return '**[Error]** This command cannot be used with other commands in the same message.'

	args = line.split(maxsplit=1)

	if len(args) != 2:
		return '**[Usage]** !roles <role name>'

	roles = [role for role in message.guild.roles if role.name == args[1]]

	if len(roles) == 0:
		return f'**[Error]** No roles found with that name ({args[1]}).'

	db = reng.db()
	cur = db.cursor()
	cur.execute('''
	SELECT r.add_on_join, r.add_on_inactive, r.bot_permission, r.admin_permission
	FROM role r
	WHERE r.role_id = ?
	''', (roles[0].id,))
	row = cur.fetchone()

	if row == None:
		role_dat = {}
	else:
		add_on_join, add_on_inactive, bot_permission, admin_permission = row
		role_dat = {'add_on_join': add_on_join, 'add_on_inactive': add_on_inactive, 'bot_permission': bot_permission, 'admin_permission': admin_permission}
		
		cur.execute('''
		SELECT r.temp, r.agreement
		FROM role_requestable r
		WHERE r.role_id = ?
		''', (roles[0].id,))
		row = cur.fetchone()

		if row == None:
			role_dat['requestable'] = False
			role_dat['requestable_temp'] = False
			role_dat['requestable_agree'] = ''
		else:
			requestable_temp, requestable_agree = row
			role_dat['requestable'] = True
			role_dat['requestable_temp'] = requestable_temp
			role_dat['requestable_agree'] = requestable_agree
		
		cur.execute('''
		SELECT r.to_add_id
		FROM role_add_when_this_removed r
		WHERE r.removed_id = ?
		''', (roles[0].id,))
		role_dat['add_when_this_role_remove'] = [to_add_id for to_add_id, in cur]
		
		cur.execute('''
		SELECT r.to_remove_id
		FROM role_remove_when_this_added r
		WHERE r.added_id = ?
		''', (roles[0].id,))
		role_dat['remove_when_this_role_add'] = [to_remove_id for to_remove_id, in cur]


	extras = {'mention': message.author.mention, 'name': roles[0].name, 'id': roles[0].id, 'guild_id': message.guild.id}
	mes = await message.channel.send(generate_message(role_dat, extras, reng))
	main_menu_dict[mes.id] = (message.author.id, dict(role_dat), extras)
	await mes.add_reaction(emoji.BRIEFCASE)
	await mes.add_reaction(emoji.GHOST)
	await mes.add_reaction(emoji.ROBOT)
	await mes.add_reaction(emoji.CROWN)
	await mes.add_reaction(emoji.MEGAPHONE)
	await mes.add_reaction(emoji.CLOCK_2)
	await mes.add_reaction(emoji.PENCIL)
	await mes.add_reaction(emoji.DOUBLE_ARROW_UP)
	await mes.add_reaction(emoji.DOUBLE_ARROW_DOWN)
	await mes.add_reaction(emoji.CHECKMARK)
	await mes.add_reaction(emoji.CROSSMARK)
	await mes.add_reaction(emoji.NO_ENTRY)

async def timer(message_id, delay, reng):
	try:
		await asyncio.sleep(delay)
		del timer_dict[message_id]
		
		db = reng.db()
		cur = db.cursor()

		cur.execute('''
		SELECT t.server_id, t.role_id, t.user_id
		FROM role_timer t
		WHERE t.message_id = ?
		''', (message_id,))

		row = cur.fetchone()

		if row != None:
			server_id, role_id, user_id = row
			await reng.client.http.remove_role(server_id, user_id, role_id, reason='Temp role expire')

			cur.execute('''
			SELECT r.to_add_id
			FROM role_add_when_this_removed r
			WHERE r.removed_id = ?
			''', (role_id,))
			add_when_this_role_remove = [to_add_id for to_add_id, in cur]

			for add_id in add_when_this_role_remove:
				try:
					await reng.client.http.add_role(server_id, user_id, add_id, reason=f'Added upon removing id({role_id})')
				except discord.errors.NotFound:
					pass

	except asyncio.CancelledError:
		db = reng.db()
		cur = db.cursor()

		cur.execute('''
		SELECT t.server_id, t.channel_id, t.role_id, t.user_id
		FROM role_timer t
		WHERE t.message_id = ?
		''', (message_id,))

		row = cur.fetchone()

		if row != None:
			server_id, channel_id, role_id, user_id = row
			await reng.client.http.remove_role(server_id, user_id, role_id, reason='Temp role cancel')
		
			cur.execute('''
			SELECT r.to_add_id
			FROM role_add_when_this_removed r
			WHERE r.removed_id = ?
			''', (role_id,))
			add_when_this_role_remove = [to_add_id for to_add_id, in cur]

			for add_id in add_when_this_role_remove:
				try:
					await reng.client.http.add_role(server_id, user_id, add_id, reason=f'Added upon removing id({role_id})')
				except discord.errors.NotFound:
					pass
			
			await reng.client.http.send_message(channel_id, f'<@{user_id}> Your {reng.client.get_guild(server_id).get_role(role_id).name} role has been removed')

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

@commands.command(condition=lambda line : commands.first_arg_match(line, 'request', 'requestrole'))
async def command_request(line, message, meta, reng):
	if message.guild == None:
		return '**[Error]** This command is only available in server channels.'

	if meta['len'] != 1:
		return '**[Error]** This command cannot be used with other commands in the same message.'

	args = line.split(maxsplit=1)
	
	roles = [role for role in message.guild.roles if role.name == args[1]]
	duration = None

	if len(roles) == 0:
		args2 = args[1].rpartition(' ')
		duration = util.parse_time(args2[2])

		roles = [role for role in message.guild.roles if role.name == args2[0]]

		if len(roles) == 0:
			return f'**[Error]** No roles found with that name ({args2[0]}).'

	db = reng.db()
	cur = db.cursor()

	cur.execute('''
	SELECT r.temp, r.agreement
	FROM role_requestable r
	WHERE r.role_id = ?
	''', (roles[0].id,))

	row = cur.fetchone()

	if row == None:
		return f'**[Error]** Role ({roles[0].name}) is not requstable.'

	requestable_temp, requestable_agree = row

	cur.execute('''
	SELECT r.to_add_id
	FROM role_add_when_this_removed r
	WHERE r.removed_id = ?
	''', (roles[0].id,))
	add_when_this_role_remove = [to_add_id for to_add_id, in cur]
	
	cur.execute('''
	SELECT r.to_remove_id
	FROM role_remove_when_this_added r
	WHERE r.added_id = ?
	''', (roles[0].id,))
	remove_when_this_role_add = [to_remove_id for to_remove_id, in cur]

	if requestable_temp:
		if roles[0] in message.author.roles:
			cur.execute('''
			SELECT r.message_id
			FROM role_timer r
			WHERE r.role_id = ? AND r.user_id = ?
			''', (roles[0].id, message.author.id))
			row = cur.fetchone()

			if row != None:
				message_id, = row
				timer_dict[message_id]['task'].cancel()
				del timer_dict[message_id]

				cur.execute('''
				DELETE FROM role_timer
				WHERE message_id = ?
				''', (message_id,))
				db.commit()
			
			add = [message.guild.get_role(role_id) for role_id in add_when_this_role_remove if message.guild.get_role(role_id) != None]
			await message.author.remove_roles(roles[0], reason='Requested')
			await message.author.add_roles(*add, reason=f'Added upon removing {roles[0].name}')
			return f'Your {roles[0].name} role has been removed'
		
		if duration == None:
			return f'**[Error]** Role ({roles[0].name}) can only be temporarily requstable. Please add a time argument.'
		
		if duration <= 0 or duration > 604800:
			return f'**[Error]** Arg 2 ({args[1]}) must represent time between 1 second and 1 week.'

		if requestable_agree:
			return '**[Not Implemented]**'

		rem = [message.guild.get_role(role_id) for role_id in remove_when_this_role_add if message.guild.get_role(role_id) != None]
		await message.author.add_roles(roles[0], reason='Requested')
		await message.author.remove_roles(*rem, reason=f'Removed upon adding {roles[0].name}')
		now = time.time()
		task = reng.client.loop.create_task(timer(message.id, duration, reng))
		timer_dict[message.id] = {'task': task, 'message_id': message.id, 'channel_id': message.channel.id, 'guild_id': message.guild.id,
			'role_id': roles[0].id, 'user_id': message.author.id, 'end_on': now + duration}
		await message.add_reaction(emoji.X)

		db = reng.db()
		db.execute('''
		INSERT INTO role_timer(message_id, channel_id, server_id, role_id, user_id, end_on)
		VALUES (?, ?, ?, ?, ?, ?)
		''', (message.id, message.channel.id, message.guild.id, roles[0].id, message.author.id, now + duration))
		db.commit()

		return f'You have been given the {roles[0].name} role. Edit, delete, or {emoji.X} the original message to remove early.'
	else:
		if roles[0] in message.author.roles:
			add = [message.guild.get_role(role_id) for role_id in add_when_this_role_remove if message.guild.get_role(role_id) != None]
			await message.author.remove_roles(roles[0], reason='Requested')
			await message.author.add_roles(*add, reason=f'Added upon removing {roles[0].name}')
			return f'Your {roles[0].name} role has been removed'
		

		if duration != None:
			return f'**[Error]** Role ({roles[0].name}) cannot be temporarily requstable. Please remove the time argument.'

		if requestable_agree:
			if any(v['user_id'] == message.author.id for v in agreement_menu_dict.values()):
				return '**[Error]** You already have an agreement pending. You cannot request this role until you have accepted or declined your previous agreement.'
			
			agree_text = f'{message.author.mention} Agreement for role {roles[0].name} in server {message.guild.name}:\n' + requestable_agree

			try:
				await message.author.create_dm()
				mes = await message.author.dm_channel.send(agree_text)
			except discord.errors.Forbidden:
				return f'**[Error]** Could not send private message.'
			
			await mes.add_reaction(emoji.CHECKMARK)
			await mes.add_reaction(emoji.CROSSMARK)
			agreement_pending_dict[mes.id] = {'role_id': roles[0].id, 'guild_id': message.guild.id, 'user_id': message.author.id, 'agreement': agree_text}
			return f'An agreement has been sent to you. React with {emoji.CHECKMARK} to accept or {emoji.CROSSMARK} to decline.'

		rem = [message.guild.get_role(role_id) for role_id in remove_when_this_role_add if message.guild.get_role(role_id) != None]
		await message.author.add_roles(roles[0], reason='Requested')
		await message.author.remove_roles(*rem, reason=f'Removed upon adding {roles[0].name}')
		return f'You have been given the {roles[0].name} role'

def on_load(reng):
	now = time.time()

	db = reng.db()
	cur = db.cursor()
	
	cur.execute('''
	DELETE FROM role_timer
	WHERE end_on < ?
	''', (now,))
	
	cur.execute('''
	SELECT t.message_id, t.channel_id, t.server_id, t.role_id, t.user_id, t.end_on
	FROM role_timer t
	''')

	db.commit()

	for message_id, channel_id, server_id, role_id, user_id, end_on in cur:
		task = reng.client.loop.create_task(timer(message_id, end_on - now, reng))
		timer_dict[message_id] = {'task': task, 'user_id': user_id}

def on_save(reng):
	reng.data['role_timers'] = [{k: v for k, v in value.items() if k != 'task'} for value in timer_dict.values()]