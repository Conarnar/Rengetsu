import commands
import time
import util
import discord

cooldown = 86400

@commands.command(condition=lambda line : commands.first_arg_match(line, 'salt'))
async def command_salt(line, message, meta, reng):
	args = line.split()

	salt_dat = reng.data.setdefault('users', {}).setdefault(str(message.author.id), {}).setdefault('salt', {})

	if len(args) == 1:
		return f'You have {salt_dat.setdefault("salt", 0)} salt.'
	elif args[1] == 'claim':
		now = time.time()
		since = now - salt_dat.setdefault('last_claim', 0)

		if since < cooldown:
			int_since = int(cooldown - since)
			h = int_since // 3600
			m = (int_since % 3600) // 60
			s = int_since % 60

			ret = 'Your next available claim is in'

			if h > 0:
				ret += f' {h} hour{"s" if h > 1 else ""}'

			if m > 0:
				ret += f' {m} minute{"s" if m > 1 else ""}'

			if s > 0 or (h == 0 and m == 0):
				ret += f' {s} second{"s" if s > 1 else ""}'

			return ret + '.'
		else:
			salt_dat['salt'] = salt_dat.setdefault("salt", 0) + 2000
			salt_dat['last_claim'] = now
			salt_dat['reminded'] = False
			return f'You gained 2000 salt. You now have {salt_dat["salt"]} salt.'
	elif args[1] == 'gift':
		if len(args) != 4:
			return '**[Usage]** !salt gift <mention> <amount>'

		match = util.user_mention_regex.fullmatch(args[2])

		if match == None:
			return f'**[Error]** Arg 2 ({args[2]}) must be a valid user mention.'

		try:
			amount = int(args[3])
		except ValueError:
			return f'**[Error]** Arg 3 ({args[3]}) must be a positive integer.'

		if amount <= 0:
			f'**[Error]** Arg 3 ({args[3]}) must be a positive integer.'

		user_id = int(match.group(1))

		if message.author.id == user_id:
			return f'**[Error]** You cannot gift salt to yourself.'

		user = reng.client.get_user(user_id)

		if user == None:
			return f'**[Error]** Arg 2 ({args[2]}) must be a valid user mention.'

		if salt_dat.setdefault("salt", 0) < amount:
			return f'**[Error]** You do not have enough salt.'

		other_salt_dat = reng.data['users'].setdefault(str(user.id), {}).setdefault('salt', {})
		other_salt_dat['salt'] = other_salt_dat.setdefault("salt", 0) + amount
		salt_dat['salt'] -= amount

		try:
			await user.create_dm()
			await user.send(f'{user.mention} You have been gifted {amount} salt from {message.author.mention}. You now have {other_salt_dat["salt"]} salt.')
		except discord.errors.Forbidden:
			pass

		return f'You gifted {amount} salt to {user.mention}. You now have {salt_dat["salt"]} salt.'
	elif args[1] == 'remind':
		salt_dat['remind'] = not salt_dat.setdefault('remind', False)
		return f'You have turned o{"n" if salt_dat["remind"] else "ff"} daily claim reminders.'


	return '**[Usage]** !salt [claim|gift|remind]'