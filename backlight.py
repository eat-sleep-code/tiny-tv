import argparse
import os
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument(dest='power', help='Specify the backlight power state', type=str, default='true')
args = parser.parse_args()


class Backlight:
	try:
		powerState = args.power.lower().strip()
	except: 
		powerState = 'true'

	try:

		if powerState == 'false' or powerState == 'off' or powerState == '0':
				subprocess.call('sudo echo 1 | sudo tee /sys/class/backlight/rpi_backlight/bl_power', shell=True)
		else:
				subprocess.call('sudo echo 0 | sudo tee /sys/class/backlight/rpi_backlight/bl_power', shell=True)

		subprocess.call('clear' if os.name == 'posix' else 'cls')
	except:
		pass
