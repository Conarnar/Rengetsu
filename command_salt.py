import commands
import time
import util
import discord

cooldown = 86400
cooldown = 10

@commands.command(condition=lambda line : commands.first_arg_match(line, 'salt'))
async def command_salt(line, message, meta, reng):
	args = line.split()
	
	db = reng.db()
	cur = db.cursor()

	cur.execute('''
	SELECT u.salt_amount, u.salt_last_claim, u.salt_remind
	FROM user u
	WHERE u.user_id = ?
	''', (message.author.id,))
	salt_amount, last_claim, salt_remind = cur.fetchone()

	if len(args) == 1:
		return f'You have {salt_amount} salt.'
	elif args[1] == 'claim':
		now = time.time()
		since = now - last_claim

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
			cur.execute('''
			UPDATE user
			SET salt_amount = ?, salt_last_claim = ?, salt_reminded = ?
			WHERE user_id = ?
			''', (salt_amount + 2000, now, False, message.author.id))
			db.commit()
			return f'You gained 2000 salt. You now have {salt_amount + 2000} salt.'
	elif args[1] == 'gift':
		if len(args) != 4:
			return '**[Usage]** !salt gift <mention> <amount>'

		match = util.user_mention_regex.fullmatch(args[2])

		if match == None:
			return f'**[Error]** Arg 2 ({args[2]}) must be a valid user mention.'

		user_id = int(match.group(1))

		user = reng.client.get_user(user_id)

		if user == None:
			return f'**[Error]** Arg 2 ({args[2]}) must be a valid user mention.'

		if message.author.id == user_id:
			return f'**[Error]** You cannot gift salt to yourself.'

		if message.author.bot:
			return f'**[Error]** You cannot gift salt to a bot.'

		try:
			transaction = int(args[3])
		except ValueError:
			return f'**[Error]** Arg 3 ({args[3]}) must be a positive integer.'

		if transaction <= 0:
			f'**[Error]** Arg 3 ({args[3]}) must be a positive integer.'

		if salt_amount < transaction:
			return f'**[Error]** You do not have enough salt.'

		cur.execute('''
		INSERT OR IGNORE INTO user(user_id, salt_amount)
		VALUES (?, ?)
		''', (user_id, transaction))

		other_salt_amount = transaction
		if cur.rowcount == 0:
			cur.execute('''
			SELECT u.salt_amount
			FROM user u
			WHERE u.user_id = ?
			''', (user_id,))

			other_salt_amount, = cur.fetchone()
			other_salt_amount += transaction
			cur.execute('''
			UPDATE user
			SET salt_amount = ?
			WHERE user_id = ?
			''', (other_salt_amount, user_id))
		
		salt_amount -= transaction
		cur.execute('''
		UPDATE user
		SET salt_amount = ?
		WHERE user_id = ?
		''', (salt_amount, message.author.id))
		db.commit()

		try:
			await user.create_dm()
			await user.send(f'{user.mention} You have been gifted {transaction} salt from {message.author.mention}. You now have {other_salt_amount} salt.')
		except discord.errors.Forbidden:
			pass

		return f'You gifted {transaction} salt. You now have {salt_amount} salt.'
	elif args[1] == 'remind':
		salt_remind = not salt_remind
		cur.execute('''
		UPDATE user
		SET salt_remind = ?
		WHERE user_id = ?
		''', (salt_remind, message.author.id))
		db.commit()

		return f'You have turned o{"n" if salt_remind else "ff"} daily claim reminders.'


	return '**[Usage]** !salt [claim|gift|remind]'