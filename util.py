import re

user_mention_regex = re.compile(r'<@!?(\d+)>')
channel_mention_regex = re.compile(r'<#(\d+)>')

time_regex = re.compile(r'(\d+)([dhms])')
time_to_seconds = {'d': 86400, 'h': 3600, 'm': 60, 's': 1}

def parse_time(string):
	try:
		return int(string)
	except ValueError:
		pass

	time = 0
	for match in time_regex.finditer(string.lower()):
		time += int(match.group(1)) * time_to_seconds[match.group(2)]
	return time