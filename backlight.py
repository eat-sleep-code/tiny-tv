import argparse
import os
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument(dest='powerState', help='Specify the backlight power state', type=bool, default=True)
args = parser.parse_args()

if args.powerState == False:
    subprocess.call('sudo echo 1 | sudo tee /sys/class/backlight/rpi_backlight/bl_power', shell=True)
else:
    subprocess.call('sudo echo 0 | sudo tee /sys/class/backlight/rpi_backlight/bl_power', shell=True)

subprocess.call('clear' if os.name == 'posix' else 'cls')
    