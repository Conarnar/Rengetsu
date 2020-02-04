import os
import json
import rengetsu
from pathlib import Path

def start(token):
	bot = rengetsu.Rengetsu(token)
	bot.start()

if __name__ == '__main__':
	file = 'reng_dat/settings.txt'
	if (os.path.isfile(file)):
		try:
			with open(file) as f:
				settings = json.load(f)
				start(settings['token'])
		except OSError:
			print('Could not read settings file:', str(e))
	else:
		try:
			token = input('Please enter token: ')
			settings = {'token' : token}
			os.makedirs(os.path.dirname(file), exist_ok=True)
			with open(file, 'w') as f:
				json.dump(settings, f, indent=4)
			print('Settings file created:', Path('reng_dat/settings.txt').absolute())
			start(token)
		except OSError as e:
			print('Could not create settings file:', str(e))