import logging
import os
import subprocess

logPath = '/home/pi/logs/tiny-tv.log'

# === Echo Control =============================================================

class Echo:
	os.environ['TERM'] = 'xterm-256color'
	def off(self):
		subprocess.run(['stty', '-echo'], check=True)
	def on(self):
		subprocess.run(['stty', 'echo'], check=True)
	def clear(self):
		subprocess.call('clear' if os.name == 'posix' else 'cls')



# === Printing & Logging ======================================================

os.environ["LIBCAMERA_LOG_LEVELS"] = "3"
logging.basicConfig(filename=logPath, level=logging.INFO, format='%(asctime)s: %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

class Console:
	def print(self, message, prefix = ' ', suffix = ' '):
		print(str(prefix) + str(message) + str(suffix)) 
	def log(self, message, prefix = ' ', suffix = ' '):
		print('\033[94m' + str(prefix) + str(message) + str(suffix)+ '\033[0m')
		logging.info(str(message))
	def debug(self, message, prefix = ' ', suffix = ' '):
		print(str(prefix) + 'DEBUG: ' + str(message) + str(suffix))
		logging.debug(str(message))
	def info(self, message, prefix = ' ', suffix = ' '):
		print(str(prefix) + 'INFO: ' + str(message) + str(suffix))
		logging.info(str(message))
	def warn(self, message, prefix = '\n ', suffix = ' '):
		print('\033[93m' + str(prefix) + 'WARNING: ' + str(message) + str(suffix) + '\033[0m')
		logging.warning(str(message))
	def error(self, message, prefix = '\n ', suffix = ' '):
		print('\033[91m' + str(prefix) + 'ERROR: ' + str(message) + str(suffix) + '\033[0m')
		logging.error(str(message))
	def critical(self, message, prefix = '\n ', suffix = '\n '):
		print('\033[91m' + str(prefix) + 'CRITICAL: ' + str(message) + str(suffix) + '\033[0m')
		logging.critical(str(message))