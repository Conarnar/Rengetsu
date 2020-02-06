import command_dice
import command_math

def load_commands(commands):
	commands.append(command_dice.c_dice)
	commands.append(command_dice.c_multiroll)
	commands.append(command_dice.c_multiroll_short)
	commands.append(command_math.c_calculate)