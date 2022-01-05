import os
import json
import rengetsu
from pathlib import Path

def start(settings):
	bot = rengetsu.Rengetsu(settings)
	bot.run()

if __name__ == '__main__':
	file = 'reng_dat/settings.txt'
	if (os.path.isfile(file)):
		try:
			with open(file) as f:
				settings = json.load(f)
				start(settings)
		except OSError as e:
			print('Error:', e)
	else:
		try:
			token = input('Please enter token: ')
			settings = {'token' : token}
			os.makedirs(os.path.dirname(file), exist_ok=True)
			with open(file, 'w') as f:
				json.dump(settings, f, indent=4)
			print('Settings file created:', Path('reng_dat/settings.txt').absolute())
			start(settings)
		except OSError as e:
			print('Could not create settings file:', e)