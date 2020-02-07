import command_dice
import command_math
import command_here
import command_role

def load_commands(commands):
	commands.append(command_dice.command_dice)
	commands.append(command_dice.command_multiroll)
	commands.append(command_dice.command_multiroll_short)
	commands.append(command_dice.command_percent)
	commands.append(command_math.command_calculate)
	commands.append(command_here.command_here)
	commands.append(command_role.command_role)

def load_menus(menus):
	menus.append(command_role.menu_main)
	menus.append(command_role.menu_agreement)
	menus.append(command_role.menu_add_remove)

def load_type_commands(type_commands):
	type_commands.append(command_role.type_command_agreement)
	type_commands.append(command_role.type_command_add_remove)