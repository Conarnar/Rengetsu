def command(condition=lambda line : True):
	def decor(command):
		command.condition = condition
		return command
	return decor

def menu(id_list):
	def decor(func):
		func.menu_id_list = id_list
		return func
	return decor

def type_command(id_list):
	def decor(func):
		func.tc_id_list = id_list
		return func
	return decor

def message_modify(id_list):
	def decor(func):
		func.mm_id_list = id_list
		return func
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