import command_dice
import command_math
import command_here
import command_role
import command_timer
import command_settings
import command_salt
import command_help
import command_db

def load_commands(commands):
	commands.append(command_dice.command_dice)
	commands.append(command_dice.command_multiroll)
	commands.append(command_dice.command_xdy)
	commands.append(command_dice.command_percent)
	commands.append(command_math.command_math)
	commands.append(command_here.command_here)
	commands.append(command_role.command_role)
	commands.append(command_role.command_request)
	commands.append(command_timer.command_timer)
	commands.append(command_settings.command_settings)
	commands.append(command_salt.command_salt)
	commands.append(command_help.command_help)
	commands.append(command_db.command_db)

def load_menus(menus):
	menus.append(command_role.menu_main)
	menus.append(command_role.menu_agreement)
	menus.append(command_role.menu_add_remove)
	menus.append(command_timer.menu_cancel)
	menus.append(command_role.menu_cancel)
	menus.append(command_role.menu_agreement_pending)

def load_type_commands(type_commands):
	type_commands.append(command_role.type_command_agreement)
	type_commands.append(command_role.type_command_add_remove)

def load_message_modifies(message_modifies):
	message_modifies.append(command_timer.modify_cancel)
	message_modifies.append(command_role.modify_cancel)

def on_load(reng):
	command_timer.on_load(reng)
	command_role.on_load(reng)