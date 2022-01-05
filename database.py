import sqlite3
import os
import json

table_dll = '''
CREATE TABLE IF NOT EXISTS server (
	server_id UNSIGNED BIG INT NOT NULL,
	inactive_days INT DEFAULT NULL,
	PRIMARY KEY (server_id)
);

CREATE TABLE IF NOT EXISTS role (
	role_id UNSIGNED BIG INT NOT NULL,
	server_id UNSIGNED BIG INT NOT NULL,
	add_on_join BOOLEAN DEFAULT FALSE,
	add_on_inactive BOOLEAN DEFAULT FALSE,
	bot_permission BOOLEAN DEFAULT FALSE,
	admin_permission BOOLEAN DEFAULT FALSE,
	PRIMARY KEY (role_id)
);

CREATE TABLE IF NOT EXISTS role_requestable (
	role_id UNSIGNED BIG INT NOT NULL,
	temp BOOLEAN DEFAULT FALSE,
	agreement TEXT,
	PRIMARY KEY (role_id),
	FOREIGN KEY (role_id) REFERENCES role(role_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS role_add_when_this_removed (
	removed_id UNSIGNED BIG INT NOT NULL,
	to_add_id UNSIGNED BIG INT NOT NULL,
	PRiMARY KEY (removed_id, to_add_id),
	FOREIGN KEY (removed_id) REFERENCES role(role_id) ON DELETE CASCADE,
	FOREIGN KEY (to_add_id) REFERENCES role(role_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS role_remove_when_this_added (
	added_id UNSIGNED BIG INT NOT NULL,
	to_remove_id UNSIGNED BIG INT NOT NULL,
	PRiMARY KEY (added_id, to_remove_id),
	FOREIGN KEY (added_id) REFERENCES role(role_id) ON DELETE CASCADE,
	FOREIGN KEY (to_remove_id) REFERENCES role(role_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS user (
	user_id UNSIGNED BIG INT NOT NULL,
	salt_amount UNSIGNED BIG INT DEFAULT 0,
	salt_last_claim DATETIME DEFAULT 0,
	salt_remind BOOLEAN DEFAULT FALSE,
	salt_reminded BOOLEAN DEFAULT FALSE,
	PRIMARY KEY (user_id)
);

CREATE TABLE IF NOT EXISTS member (
	user_id UNSIGNED BIG INT NOT NULL,
	server_id UNSIGNED BIG INT NOT NULL,
	last_msg DATETIME DEFAULT 0,
	PRIMARY KEY (user_id, server_id),
	FOREIGN KEY (user_id) REFERENCES user(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS channel (
	channel_id UNSIGNED BIG INT NOT NULL,
	server_id UNSIGNED BIG INT NOT NULL,
	msg_log BOOLEAN DEFAULT FALSE,
	user_log BOOLEAN DEFAULT FALSE,
	PRIMARY KEY (channel_id)
);

CREATE TABLE IF NOT EXISTS timer (
	message_id UNSIGNED BIG INT NOT NULL,
	channel_id UNSIGNED BIG INT NOT NULL,
	user_id UNSIGNED BIG INT NOT NULL,
	text TEXT NOT NULL,
	set_on REAL NOT NULL,
	end_on REAL NOT NULL,
	PRIMARY KEY (message_id)
);

CREATE TABLE IF NOT EXISTS role_timer (
	message_id UNSIGNED BIG INT NOT NULL,
	channel_id UNSIGNED BIG INT NOT NULL,
	server_id UNSIGNED BIG INT NOT NULL,
	role_id UNSIGNED BIG INT NOT NULL,
	user_id UNSIGNED BIG INT NOT NULL,
	end_on REAL NOT NULL,
	PRIMARY KEY (message_id),
	FOREIGN KEY (role_id) REFERENCES role(role_id) ON DELETE CASCADE
);
'''

def initialize_data(db_file, logger):
	if os.path.isfile(db_file):
		logger.info('Database file found')
	else:
		logger.info('No database file found, initializing')
		con = create_connection(db_file)
		con.executescript(table_dll)

		if os.path.isfile('reng_dat/rengetsu.dat'):
			logger.info('rengetsu.dat found, attempting to convert data')

			with open('reng_dat/rengetsu.dat') as f:
				old_data = json.load(f)
				convert_data(old_data, db_file)


def create_connection(db_file):
	return sqlite3.connect(db_file)

def convert_data(old_data, db_file):
	db = create_connection(db_file)
	cur = db.cursor()

	for server_id in old_data.get('servers', {}):
		server_dat = old_data['servers'][server_id]
		settings_dat = server_dat.get('settings', {})
		cur.execute('''
		INSERT INTO server(server_id, inactive_days)
		VALUES (?, ?)
		''', (server_id, settings_dat.get('inactive', 0)))

		for role_id in server_dat.get('roles', {}):
			role_dat = server_dat['roles'][role_id]
			cur.execute('''
			INSERT INTO role(role_id, server_id, add_on_join, add_on_inactive, bot_permission)
			VALUES (?, ?, ?, ?, ?)
			''', (role_id, server_id, role_dat.get('add_on_join', False), role_dat.get('add_on_inactive', False), role_dat.get('bot_permission', False)))

			if role_dat.get('requestable', False):
				cur.execute('''
				INSERT INTO role_requestable(role_id, temp, agreement)
				VALUES (?, ?, ?)
				''', (role_id, role_dat.get('requestable_temp', False), role_dat.get('requestable_agree', '')))

			for add_when_this_remove_id in role_dat.get('add_when_this_role_remove', []):
				cur.execute('''
				INSERT INTO role_add_when_this_removed(removed_id, to_add_id)
				VALUES (?, ?)
				''', (role_id, add_when_this_remove_id))

			for remove_when_this_add_id in role_dat.get('remove_when_this_role_add', []):
				cur.execute('''
				INSERT INTO role_remove_when_this_added(added_id, to_remove_id)
				VALUES (?, ?)
				''', (role_id, remove_when_this_add_id))
		
		logging_channel_ids = settings_dat.get('logging', [])
		msglog_channel_ids = settings_dat.get('msglog', [])

		for channel_id in set(logging_channel_ids + msglog_channel_ids):
			cur.execute('''
			INSERT INTO channel(channel_id, server_id, msg_log, user_log)
			VALUES (?, ?, ?, ?)
			''', (channel_id, server_id, channel_id in msglog_channel_ids, channel_id in logging_channel_ids))

		
	for user_id in old_data.get('users', {}):
		user_dat = old_data['users'][user_id]
		salt_dat = user_dat.get('salt', {})
		cur.execute('''
		INSERT INTO user(user_id, salt_amount, salt_last_claim, salt_remind, salt_reminded)
		VALUES (?, ?, ?, ?, ?)
		''', (user_id, salt_dat.get('salt', 0), salt_dat.get('last_claim', 0), salt_dat.get('remind', False), salt_dat.get('reminded', False)))
	
	db.commit()

'''
CREATE TABLE IF NOT EXISTS channel (
	channel_id UNSIGNED BIG INT NOT NULL,
	server_id UNSIGNED BIG INT NOT NULL,
	msg_log BOOLEAN DEFAULT FALSE,
	user_log BOOLEAN DEFAULT FALSE,
	PRIMARY KEY (channel_id)
);
'''