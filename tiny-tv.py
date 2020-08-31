import argparse
import keyboard
import os
import subprocess
import shutil
import sys
import time
import youtube_dl

version = "2020.08.31"

# === Argument Handling ========================================================

parser = argparse.ArgumentParser()
parser.add_argument(dest='input', help='Select the video to be played', type=str)
parser.add_argument('--saveAs', dest='saveAs', help='Enter the name you would like the file saved as', type=str) # USED IF DOWNLOADING FROM YOUTUBE ONLY
parser.add_argument('--maximumVideoHeight', dest='maximumVideoHeight', help='Set the maximum height (in pixels) for downloaded videos', type=str) # USED IF DOWNLOADING FROM YOUTUBE ONLY
parser.add_argument('--category', dest='category', help='Select the category', type=str)
parser.add_argument('--removeVerticalBars', dest='removeVerticalBars', help='Remove the vertical black bars from the input file (time-intensive)', type=bool)
parser.add_argument('--removeHorizontalBars', dest='removeHorizontalBars', help='Remove the horizontal black bars from the input file (time-intensive)', type=bool)
parser.add_argument('--volume', dest='volume', help='Set the initial volume', type=int)

args = parser.parse_args()

input = args.input or ''

saveAs = args.saveAs or 'YOUTUBEID'


maximumVideoHeight = args.maximumVideoHeight = 720
try:
	maximumVideoHeight = int(maximumVideoHeight)
except:
	maximumVideoHeightlume = 720


category = args.category or ''
videoFolder = '/home/pi/videos/'
videoCategoryFolder = videoFolder + category + '/'


removeVerticalBars = args.removeVerticalBars or False
if removeVerticalBars != True:
	removeVerticalBars = False


removeHorizontalBars = args.removeHorizontalBars or False
if removeHorizontalBars != True:
	removeHorizontalBars = False


volume = args.volume or 400
try:
	volume = int(volume)
except:
	volume = 400


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
	
	print('\n Tiny TV ' + version )
	print('\n ----------------------------------------------------------------------\n')
		
	while True:
		if keyboard.is_pressed('ctrl+c') or keyboard.is_pressed('esc'):
			# clear()
			echoOn()
			break
		

		video = input
		if input.find('youtube.com') != -1:
			print(' Starting download of video... ')
			youtubeDownloadOptions = { 
				'outtmpl': videoCategoryFolder + '%(id)s.%(ext)s',
				'format': 'best[height=' + str(maximumVideoHeight) + ']'
			}
			with youtube_dl.YoutubeDL(youtubeDownloadOptions) as youtubeDownload:
				info = youtubeDownload.extract_info(input)
				video = info.get('id', None) + '.' + info.get('ext', None)
				
			print(' Setting the owner of the file to current user...')
			shutil.chown(videoCategoryFolder + video, user='pi', group='pi')
			if saveAs != 'YOUTUBEID':
				try:
					os.rename(videoCategoryFolder + video, videoCategoryFolder + saveAs)
					video = saveAs
				except Exception as ex:
					print(str(ex))
		if removeVerticalBars == True:
			print(' Starting removal of vertical black bars (this will take a while)... ')
			subprocess.call('ffmpeg -i "' + videoCategoryFolder + video + '" -filter:v "crop=ih/9*16:ih" -c:v libx264 -crf 23 -preset veryfast -c:a copy "' + videoCategoryFolder + '~' + video + '"' , shell=True)
			os.remove(videoCategoryFolder + video)
			os.rename(videoCategoryFolder + '~' + video, videoCategoryFolder + saveAs)
			shutil.chown(videoCategoryFolder + video, user='pi', group='pi')
			
		elif removeHorizontalBars == True:
			print(' Starting removal of horizontal black bars (this will take a while)... ')
			subprocess.call('ffmpeg -i "' + videoCategoryFolder + video + '" -filter:v "crop=ih/3*4:ih" -c:v libx264 -crf 23 -preset veryfast -c:a copy "' + videoCategoryFolder + '~' + video + '"', shell=True)
			os.remove(videoCategoryFolder + video)
			os.rename(videoCategoryFolder + '~' + video, videoCategoryFolder + saveAs)
			shutil.chown(videoCategoryFolder + video, user='pi', group='pi')
	
		print(' Starting playback... ')
		videoFullPath = videoCategoryFolder + str(video)
		subprocess.call('omxplayer --loop -o alsa --vol ' + str(volume) + ' "' + videoFullPath + '"', shell=True)
		sys.exit(0)


except KeyboardInterrupt:
	echoOn()
	sys.exit(1)

else:
	sys.exit(0)
