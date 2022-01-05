import commands
import discord

@commands.command(condition=lambda line : commands.first_arg_match(line, 'db'))
async def command_db(line, message, meta, reng):
	app_info = await reng.client.application_info()
	if app_info.owner.id != message.author.id:
		return '**[Error]** You do not have permission to use this command.'
	
	args = line.split(maxsplit=1)

	if len(args) != 2:
		return '**[Usage]** !db <query>'
	
	db = reng.db()

	try:
		cur = db.execute(args[1])
		db.commit()
	except Exception as e:
		return repr(e)
	
	if cur.rowcount == -1:
		rows = cur.fetchall()
		return f'Results: {len(rows)} rows\n' + '\n'.join(str(row) for row in rows)
	else:
		return f'{cur.rowcount} rows changed'