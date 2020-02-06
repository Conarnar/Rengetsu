def command(condition=lambda line : True):
	def decor(command):
		command.condition = condition
		return command
	return decor

def first_arg_match(line, *match):
	args = line.split()
	if len(args) == 0:
		return False
	for s in match:
		if args[0] == s:
			return True
	return False

class SkipCommand(Exception):
	pass