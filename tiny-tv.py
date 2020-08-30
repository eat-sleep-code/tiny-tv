import argparse
import keyboard
import os
import subprocess
import sys
import time

version = "2020.08.30"

# === Argument Handling ========================================================

parser = argparse.ArgumentParser()
parser.add_argument('--input', dest='input', help='Select the video to be played')
parser.add_argument('--category', dest='category', help='Select the category')
parser.add_argument('--volume', dest='volume', help='Set the initial volume')
parser.add_argument('--removeVerticalBars', dest='removeVerticalBars', help='Remove the vertical black bars from the input file (time-intensive)')
parser.add_argument('--removeHorizontalBars', dest='removeVerticalBars', help='Remove the horizontal black bars from the input file (time-intensive)')

args = parser.parse_args()


input = args.input or ''

volume = args.volume or 400
try:
	volume = int(volume)
except:
	volume = 400


category = args.category or ''
videoFolder = '/home/pi/videos/'
videoCategoryFolder = videoFolder + category + '/'

removeVerticalBars = args.removeVerticalBars or False
if removeVerticalBars != True:
	removeVerticalBars = False


removeHorizontalBars = args.removeHorizontalBars or False
if removeHorizontalBars != True:
	removeHorizontalBars = False


# === Echo Control =============================================================

def echoOff():
	subprocess.run(['stty', '-echo'], check=True)
def echoOn():
	subprocess.run(['stty', 'echo'], check=True)
def clear():
	subprocess.call('clear' if os.name == 'posix' else 'cls')
clear()


# === Functions ================================================================

def getVideoPath(inputPath):
	try:
		os.makedirs(inputPath, exist_ok = True)
	except OSError:
		print ('\n ERROR: Creation of the output folder ' + inputPath + ' failed!' )
		echoOn()
		quit()
	else:
		return inputPath

		
# ------------------------------------------------------------------------------


# === Tiny TV =============================================================

try: 
	os.chdir('/home/pi')
	global category
	global input 
	
	global volume
	print('\n Tiny TV ' + version )
	print('\n ----------------------------------------------------------------------\n')
		
	while True:
		if keyboard.is_pressed('ctrl+c') or keyboard.is_pressed('esc'):
			# clear()
			echoOn()
			break
		
		while True:	
			video = input
			if input.fine('youtube.com') != -1:
				print(' Starting download of video... ')
				subprocess.call('youtube-dl -f 18 ' + input, shell=True)
				video = subprocess.call('youtube-dl --get-filename ' + input, shell=True)
			if removeVerticalBars == True:
				print(' Starting removal of vertical black bars (this will take a while)... ')
				videoToConvertPath = videoCategoryFolder + input;
				subprocess.call('ffmpeg -i "' + videoToConvertPath +'" -filter:b "crop=ih/3*4:ih" -c:v libx264 -crf 23 -preset veryfast -c:a copy debarred.mp4 && sudo rm -Rf ' + videoToConvertPath + ' && mv debarred.mp4 ' + videoToConvertPath + ' , shell=True)
			elif removeHorizontalBars == True:
				print(' Starting removal of horizontal black bars (this will take a while)... ')
				subprocess.call('ffmpeg -i "' + videoToConvertPath +'" -filter:b "crop=ih/9*16:ih" -c:v libx264 -crf 23 -preset veryfast -c:a copy debarred.mp4 && sudo rm -Rf ' + videoToConvertPath + ' && mv debarred.mp4 ' + videoToConvertPath + ' , shell=True)
				subprocess.call('', shell=True)
			
			videoFullPath = videoCategoryFolder + video
			subprocess.call('omxplayer -o alsa --vol ' + str(volume) + '"' + videoFullPath + '" --loop', shell=True)


except KeyboardInterrupt:
	echoOn()
	sys.exit(1)

else:
	sys.exit(0)
