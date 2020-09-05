import argparse
import keyboard
import os
import subprocess
import shutil
import sys
import time
import youtube_dl

version = '2020.09.05'

# === Argument Handling ========================================================

parser = argparse.ArgumentParser()
parser.add_argument(dest='input', help='Select the video to be played', type=str)
parser.add_argument('--saveAs', dest='saveAs', help='Enter the name you would like the file saved as', type=str) # USED IF DOWNLOADING FROM YOUTUBE ONLY
parser.add_argument('--category', dest='category', help='Select the category', type=str)
parser.add_argument('--maximumVideoHeight', dest='maximumVideoHeight', help='Set the maximum height (in pixels) for the video', type=int) 
parser.add_argument('--removeVerticalBars', dest='removeVerticalBars', help='Remove the vertical black bars from the input file (time-intensive)', type=bool)
parser.add_argument('--removeHorizontalBars', dest='removeHorizontalBars', help='Remove the horizontal black bars from the input file (time-intensive)', type=bool)
parser.add_argument('--resize', dest='resize', help='Resize but do not crop', type=bool)
parser.add_argument('--volume', dest='volume', help='Set the initial volume', type=int)
args = parser.parse_args()


input = args.input or ''

# ------------------------------------------------------------------------------

saveAs = args.saveAs or 'YOUTUBEID'

# ------------------------------------------------------------------------------

maximumVideoHeight = args.maximumVideoHeight = 480
try:
	maximumVideoHeight = int(maximumVideoHeight)
except:
	maximumVideoHeight = 480

# ------------------------------------------------------------------------------

category = args.category or ''
videoFolder = '/home/pi/videos/'
videoCategoryFolder = videoFolder + category + '/'

# ------------------------------------------------------------------------------

removeVerticalBars = args.removeVerticalBars or False
if removeVerticalBars != True:
	removeVerticalBars = False

# ------------------------------------------------------------------------------

removeHorizontalBars = args.removeHorizontalBars or False
if removeHorizontalBars != True:
	removeHorizontalBars = False

# ------------------------------------------------------------------------------

resize = args.resize or False
if resize != True:
	resize = False

# ------------------------------------------------------------------------------

volume = args.volume or 400
try:
	volume = int(volume)
except:
	volume = 400

# ------------------------------------------------------------------------------

playCount = 0

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


# === Tiny TV ==================================================================

try: 
	os.chdir('/home/pi')
	
	print('\n Tiny TV ' + version )
	print('\n ----------------------------------------------------------------------\n')
		
	while True:
		if keyboard.is_pressed('ctrl+c') or keyboard.is_pressed('esc'):
			# clear()
			echoOn()
			break
		
		if input.find('.') == -1 and input.find(';') == -1:
			input = input + '.mp4'
		video = input
		
		
		# --- YouTube Download -------------------------------------------------

		if input.find('youtube.com') != -1:
			print(' Starting download of video... ')
			downloadHeight = 720
			if maximumVideoHeight >= 4320: # Future product
				downloadHeight = 4320
			elif maximumVideoHeight >= 2160: # Minimum Raspberry Pi 4
				downloadHeight = 2160
			elif maximumVideoHeight >= 1080: # Minimum Raspberry Pi 3B+
				downloadHeight = 1080
			youtubeDownloadOptions = { 
				'outtmpl': videoCategoryFolder + '%(id)s.%(ext)s',
				'format': 'best[height=' + str(downloadHeight) + ']'
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
		

		# --- Pillar Box / Letter Box Removal ----------------------------------

		if removeVerticalBars == True:
			print(' Starting removal of vertical black bars (this will take a while)... ')
			subprocess.call('ffmpeg -i "' + videoCategoryFolder + video + '" -filter:v "crop=ih/3*4:ih,scale=-2:' + str(maximumVideoHeight) + ',setsar=1" -c:v libx264 -crf 27 -preset veryfast -c:a copy "' + videoCategoryFolder + '~' + video + '"' , shell=True)
			os.remove(videoCategoryFolder + video)
			os.rename(videoCategoryFolder + '~' + video, videoCategoryFolder + video)
			shutil.chown(videoCategoryFolder + video, user='pi', group='pi')
			
		elif removeHorizontalBars == True:
			print(' Starting removal of horizontal black bars (this will take a while)... ')
			subprocess.call('ffmpeg -i "' + videoCategoryFolder + video + '" -filter:v "crop=iw:iw/16*9,scale=-2:' + str(maximumVideoHeight) + ',setsar=1" -c:v libx264 -crf 27 -preset veryfast -c:a copy "' + videoCategoryFolder + '~' + video + '"', shell=True)
			os.remove(videoCategoryFolder + video)
			os.rename(videoCategoryFolder + '~' + video, videoCategoryFolder + video)
			shutil.chown(videoCategoryFolder + video, user='pi', group='pi')

		# --- Resize only ------------------------------------------------------

		if removeVerticalBars == True:
			print(' Starting resize to maximum video height (this will take a while)... ')
			subprocess.call('ffmpeg -i "' + videoCategoryFolder + video + '" -filter:v "scale=-2:' + str(maximumVideoHeight) + ',setsar=1" -c:v libx264 -crf 27 -preset veryfast -c:a copy "' + videoCategoryFolder + '~' + video + '"' , shell=True)
			os.remove(videoCategoryFolder + video)
			os.rename(videoCategoryFolder + '~' + video, videoCategoryFolder + video)
			shutil.chown(videoCategoryFolder + video, user='pi', group='pi')
		
		# --- Playback ---------------------------------------------------------

		playCount = 0
		while playCount >= 0:
			playCount += 1
			print('\n Starting playback ' + str(playCount) + '...')
			videoFullPath = videoCategoryFolder + str(video)
			subprocess.call('omxplayer -o alsa --vol ' + str(volume) + ' "' + videoFullPath + '"', shell=True)
			time.sleep(10)
			
		sys.exit(0)

except KeyboardInterrupt:
	echoOn()
	sys.exit(1)

else:
	sys.exit(0)
